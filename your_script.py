import tkinter as tk
from tkinter import messagebox
import subprocess
import configparser
import os
import sys
import ctypes
import threading
import time

# Tray support
try:
    import pystray
    from PIL import Image, ImageDraw
except Exception:
    pystray = None
    Image = None

CONFIG_FILE = 'config.ini'
INTERFACE_NAME = "以太网"  # 如果你的网卡名称不是以太网，改成实际的名称（可在命令行运行 `netsh interface show interface` 获取）

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    # 重新启动脚本，并要求管理员权限
    # sys.executable 在打包成 exe 后会是 exe 的路径，这样可以正确申请 UAC
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
    sys.exit()

def save_config():
    config = configparser.ConfigParser()
    config['NETWORK1'] = {
        'ip': ip_entry1.get(),
        'subnet': subnet_entry1.get(),
        'gateway': gateway_entry1.get(),
        'dns1': dns1_entry1.get(),
        'dns2': dns2_entry1.get()
    }
    config['NETWORK2'] = {
        'ip': ip_entry2.get(),
        'subnet': subnet_entry2.get(),
        'gateway': gateway_entry2.get(),
        'dns1': dns1_entry2.get(),
        'dns2': dns2_entry2.get()
    }
    with open(CONFIG_FILE, 'w', encoding='utf-8') as configfile:
        config.write(configfile)
    messagebox.showinfo("成功", "已保存配置")

def load_config():
    if os.path.exists(CONFIG_FILE):
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE, encoding='utf-8')
        if config.has_section('NETWORK1'):
            network1 = config['NETWORK1']
            ip_entry1.delete(0, tk.END)
            ip_entry1.insert(0, network1.get('ip', ''))
            subnet_entry1.delete(0, tk.END)
            subnet_entry1.insert(0, network1.get('subnet', ''))
            gateway_entry1.delete(0, tk.END)
            gateway_entry1.insert(0, network1.get('gateway', ''))
            dns1_entry1.delete(0, tk.END)
            dns1_entry1.insert(0, network1.get('dns1', ''))
            dns2_entry1.delete(0, tk.END)
            dns2_entry1.insert(0, network1.get('dns2', ''))
        if config.has_section('NETWORK2'):
            network2 = config['NETWORK2']
            ip_entry2.delete(0, tk.END)
            ip_entry2.insert(0, network2.get('ip', ''))
            subnet_entry2.delete(0, tk.END)
            subnet_entry2.insert(0, network2.get('subnet', ''))
            gateway_entry2.delete(0, tk.END)
            gateway_entry2.insert(0, network2.get('gateway', ''))
            dns1_entry2.delete(0, tk.END)
            dns1_entry2.insert(0, network2.get('dns1', ''))
            dns2_entry2.delete(0, tk.END)
            dns2_entry2.insert(0, network2.get('dns2', ''))

def get_network_info():
    # 使用字符串命令并 shell=True 在 Windows 上更稳定
    result = subprocess.run('ipconfig', capture_output=True, text=True, shell=True)
    output_lines = result.stdout.splitlines()
    # 过滤掉虚拟交换机项（如果需要）
    filtered_lines = [line for line in output_lines if 'vEthernet (Default Switch)' not in line]
    return "\n".join(filtered_lines)

def refresh_network_info():
    network_info.set(get_network_info())

def set_auto_ip():
    try:
        cmd_addr = f'netsh interface ip set address name="{INTERFACE_NAME}" source=dhcp'
        cmd_dns = f'netsh interface ip set dns name="{INTERFACE_NAME}" source=dhcp'
        subprocess.run(cmd_addr, check=True, shell=True)
        subprocess.run(cmd_dns, check=True, shell=True)
        refresh_network_info()
        messagebox.showinfo("成功", "IP已自动获取")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("错误", f"自动获取IP时出错:\n{e}")

def set_manual_ip(ip, subnet, gateway, dns1, dns2):
    try:
        if not ip or not subnet or not gateway:
            messagebox.showwarning("缺少参数", "请填写 IP、子网掩码和网关")
            return
        cmd_addr = f'netsh interface ip set address name="{INTERFACE_NAME}" static {ip} {subnet} {gateway}'
        cmd_dns = f'netsh interface ip set dns name="{INTERFACE_NAME}" static {dns1}'
        subprocess.run(cmd_addr, check=True, shell=True)
        subprocess.run(cmd_dns, check=True, shell=True)
        if dns2:
            cmd_dns2 = f'netsh interface ip add dns name="{INTERFACE_NAME}" {dns2} index=2'
            subprocess.run(cmd_dns2, check=True, shell=True)
        refresh_network_info()
        messagebox.showinfo("成功", "IP已设置为手动配置")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("错误", f"设置IP时出错:\n{e}")

# ---- GUI ----
root = tk.Tk()
root.title("自动切换IP和DNS")

# 当窗口最小化或关闭时隐藏到托盘
def on_closing():
    try:
        root.withdraw()
        if tray_icon:
            # 显示提示（可选）
            tray_icon.visible = True
    except:
        root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# 网络信息显示区
current_network_frame = tk.LabelFrame(root, text="当前网络信息", padx=10, pady=10)
current_network_frame.pack(side=tk.LEFT, padx=10, pady=10)

network_info = tk.StringVar()
network_info.set(get_network_info())
current_network_info = tk.Label(current_network_frame, textvariable=network_info, wraplength=350, justify=tk.LEFT)
current_network_info.pack()

# 刷新按钮
refresh_button = tk.Button(current_network_frame, text="刷新", command=refresh_network_info)
refresh_button.pack(pady=10)

# 配置输入区
config_frame = tk.Frame(root)
config_frame.pack(side=tk.RIGHT, padx=10, pady=10)

# 自动获取IP按钮
auto_get_ip_button = tk.Button(config_frame, text="自动获取IP", command=set_auto_ip)
auto_get_ip_button.grid(row=0, column=0, columnspan=4, pady=10, sticky="ew")

# IP配置标签和输入框排列——第一组
ip_label1 = tk.Label(config_frame, text="IP地址1:")
ip_label1.grid(row=1, column=0, sticky=tk.E)
ip_entry1 = tk.Entry(config_frame)
ip_entry1.grid(row=1, column=1, padx=(0, 10))

subnet_label1 = tk.Label(config_frame, text="子网掩码1:")
subnet_label1.grid(row=2, column=0, sticky=tk.E)
subnet_entry1 = tk.Entry(config_frame)
subnet_entry1.grid(row=2, column=1, padx=(0, 10))

gateway_label1 = tk.Label(config_frame, text="网关1:")
gateway_label1.grid(row=3, column=0, sticky=tk.E)
gateway_entry1 = tk.Entry(config_frame)
gateway_entry1.grid(row=3, column=1, padx=(0, 10))

dns1_label1 = tk.Label(config_frame, text="DNS1:")
dns1_label1.grid(row=4, column=0, sticky=tk.E)
dns1_entry1 = tk.Entry(config_frame)
dns1_entry1.grid(row=4, column=1, padx=(0, 10))

dns2_label1 = tk.Label(config_frame, text="DNS2:")
dns2_label1.grid(row=5, column=0, sticky=tk.E)
dns2_entry1 = tk.Entry(config_frame)
dns2_entry1.grid(row=5, column=1, padx=(0, 10))

manual_ip_button1 = tk.Button(config_frame, text="手动获取IP模块1",
                              command=lambda: set_manual_ip(ip_entry1.get(), subnet_entry1.get(), gateway_entry1.get(), dns1_entry1.get(), dns2_entry1.get()))
manual_ip_button1.grid(row=6, column=0, columnspan=2, pady=10, sticky="ew")

# IP配置标签和输入框排列——第二组
ip_label2 = tk.Label(config_frame, text="IP地址2:")
ip_label2.grid(row=1, column=2, sticky=tk.E)
ip_entry2 = tk.Entry(config_frame)
ip_entry2.grid(row=1, column=3, padx=(0, 10))

subnet_label2 = tk.Label(config_frame, text="子网掩码2:")
subnet_label2.grid(row=2, column=2, sticky=tk.E)
subnet_entry2 = tk.Entry(config_frame)
subnet_entry2.grid(row=2, column=3, padx=(0, 10))

gateway_label2 = tk.Label(config_frame, text="网关2:")
gateway_label2.grid(row=3, column=2, sticky=tk.E)
gateway_entry2 = tk.Entry(config_frame)
gateway_entry2.grid(row=3, column=3, padx=(0, 10))

dns1_label2 = tk.Label(config_frame, text="DNS1:")
dns1_label2.grid(row=4, column=2, sticky=tk.E)
dns1_entry2 = tk.Entry(config_frame)
dns1_entry2.grid(row=4, column=3, padx=(0, 10))

dns2_label2 = tk.Label(config_frame, text="DNS2:")
dns2_label2.grid(row=5, column=2, sticky=tk.E)
dns2_entry2 = tk.Entry(config_frame)
dns2_entry2.grid(row=5, column=3, padx=(0, 10))

manual_ip_button2 = tk.Button(config_frame, text="手动获取IP模块2",
                              command=lambda: set_manual_ip(ip_entry2.get(), subnet_entry2.get(), gateway_entry2.get(), dns1_entry2.get(), dns2_entry2.get()))
manual_ip_button2.grid(row=6, column=2, columnspan=2, pady=10, sticky="ew")

# 保存配置按钮
save_button = tk.Button(config_frame, text="保存配置", command=save_config)
save_button.grid(row=7, column=0, columnspan=4, pady=10, sticky="ew")

# 加载配置
load_config()

# ---- 托盘图标和菜单 ----
tray_icon = None

def create_image():
    # 生成一个简单的 64x64 的图标（白底蓝圆），如果 PIL 可用
    if Image is None:
        return None
    size = 64
    image = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    d = ImageDraw.Draw(image)
    d.ellipse((4, 4, size-4, size-4), fill=(20, 100, 200, 255))
    return image

def apply_profile1():
    # 从界面读取第一个配置并应用
    ip = ip_entry1.get()
    subnet = subnet_entry1.get()
    gateway = gateway_entry1.get()
    dns1 = dns1_entry1.get()
    dns2 = dns2_entry1.get()
    set_manual_ip(ip, subnet, gateway, dns1, dns2)

def apply_profile2():
    ip = ip_entry2.get()
    subnet = subnet_entry2.get()
    gateway = gateway_entry2.get()
    dns1 = dns1_entry2.get()
    dns2 = dns2_entry2.get()
    set_manual_ip(ip, subnet, gateway, dns1, dns2)

def show_window():
    # 将窗口显示到前台
    try:
        root.deiconify()
        root.after(100, lambda: root.lift())
    except:
        pass

def exit_app():
    try:
        if tray_icon:
            tray_icon.stop()
    except:
        pass
    try:
        root.destroy()
    except:
        os._exit(0)

def tray_thread():
    global tray_icon
    if pystray is None:
        return
    image = create_image()
    menu = pystray.Menu(
        pystray.MenuItem('显示主窗口', lambda _: root.after(0, show_window)),
        pystray.MenuItem('切换到模块1', lambda _: root.after(0, apply_profile1)),
        pystray.MenuItem('切换到模块2', lambda _: root.after(0, apply_profile2)),
        pystray.MenuItem('自动获取IP', lambda _: root.after(0, set_auto_ip)),
        pystray.MenuItem('刷新网络信息', lambda _: root.after(0, refresh_network_info)),
        pystray.MenuItem('退出', lambda _: root.after(0, exit_app))
    )
    tray_icon = pystray.Icon("ip-switcher", image, "IP切换器", menu)
    tray_icon.run()

# 如果 pystray 可用，启动托盘线程
if pystray is not None:
    t = threading.Thread(target=tray_thread, daemon=True)
    t.start()
else:
    # 没有安装 pystray 或 PIL，会在 GUI 中给出提示，但程序仍然可用
    def no_tray_warning():
        messagebox.showwarning("托盘功能不可用", "未检测到 pystray 或 PIL(Pillow)。右键任务栏图标不可用。\n\n安装: pip install pystray pillow")
    root.after(1000, no_tray_warning)

# 启动主循环
root.mainloop()