import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import requests
import threading
import queue
import datetime
import natsort
import re
import json
from login_test import LoginSystem


class LoginFrame(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        # 创建LoginSystem类的实例对象
        self.login_system = LoginSystem()
        self.init_ui()
    
    def init_ui(self):
        # 创建窗口
        self.master.title("Login")

        #创建用户框
        self.username_label = tk.Label(self, text="Username:")
        self.username_label.pack()
        self.username_entry = tk.Entry(self)
        self.username_entry.pack()


        self.password_label = tk.Label(self, text="Password:")
        self.password_label.pack()
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack()

        self.remember_var = tk.BooleanVar(value=False)
        self.remember_checkbox = tk.Checkbutton(self, text="记住我", variable=self.remember_var)
        self.remember_checkbox.pack()

        self.login_button = tk.Button(self, text="Login", command=self.on_login_button_clicked)
        self.login_button.pack()

        # 放置窗口在屏幕中心
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        window_width = 500
        window_height = 400
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.master.geometry(f"{window_width}x{window_height}+{x}+{y}")

    #登录按钮点击事件
    def on_login_button_clicked(self):
            # 获取用户名和密码
            username = self.username_entry.get()
            password = self.password_entry.get()
            remember = self.remember_var.get()

            # 在新线程中进行登录操作
            login_thread = threading.Thread(target=self.do_login, args=(remember, username, password, self.on_login_result))
            login_thread.start()

    #登录界面
    def do_login(self, remember, username, password, callback):
        # 进行登录操作
        success = self.login_system.run(remember, username, password)
        callback(success)

    #登录成功后的函数
    def on_login_result(self, success):
        print(success)
        if success:
            self.master.after(0, self.switch_to_new_frame, self.login_system.cookies)
        else:
            messagebox.showwarning("Login failed", "账号或密码输入有误")

    def switch_to_new_frame(self, login_cookie):
            self.master.destroy() # close the login window
            new_frame = SearchFrame(login_cookie)
            new_frame.master.title("查询编号段最大值")
            new_frame.pack()

class SearchFrame(tk.Frame):
    SEARCH_URL = "http://127.0.0.1/ViewHrmsEmp/SetSearch"
    GET_ALL_URL = "http://127.0.0.1/ViewHrmsEmp/GetAll"

    def __init__(self, login_cookie=None,master=None):
        super().__init__(master)
        self.login_cookie = login_cookie
        self.default_values = self.get_default_emp_no()
        self.queue = queue.Queue()
        self.create_widgets()
        self.process_queue()



    #创建界面
    def create_widgets(self):
        # 展示预先的编号查询结果
        self.show_table()
        # Create query frame
        self.query_frame = tk.Frame(self.master)
        self.query_frame.pack(side="bottom")

        self.pvalue0_label = tk.Label(self.query_frame, text="输入编号段开头值：")
        self.pvalue0_label.grid(row=0, column=0)
        self.pvalue0_entry = tk.Entry(self.query_frame)
        self.pvalue0_entry.grid(row=0, column=1)

        self.run_button = tk.Button(self.query_frame, text="查询", command=self.fetch_max_emp_no)
        self.run_button.grid(row=0, column=2)

        self.result_label = tk.Label(self.query_frame, text="")
        self.result_label.grid(row=1, column=0, columnspan=3)

        # 放置窗口在屏幕中心
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        window_width = 500
        window_height = 400
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.master.geometry(f"{window_width}x{window_height}+{x}+{y}")
    

    #预先展示结果表格
    def show_table(self):
        self.master.title("校园卡号查询")

        # 设置主题
        style = ttk.Style()
        style.theme_use("clam")  # 可以尝试不同的主题，如'themed', 'alt', 'default', 'classic', 'vista'

        # 设置自定义颜色
        style.configure("Treeview", background="#383838", foreground="white", fieldbackground="#383838", font=("Helvetica", 10))
        style.configure("Treeview.Heading", background="dark green", foreground="white", font=("Helvetica", 12, "bold"))

        # 创建Treeview
        self.tree = ttk.Treeview(self.master, columns=("序号","编号", "目前最大编号"), show="headings", style="Treeview")
        self.tree.heading(0, text="序号")
        self.tree.heading(1, text="编号")
        self.tree.heading(2, text="目前最大编号")
        
        # 设置列宽
        self.tree.column(0, width=50, anchor="center")
        self.tree.column(1, width=150, anchor="center")
        self.tree.column(2, width=200, anchor="center")

        # 展示Treeview
        self.tree.pack(fill=tk.BOTH, expand=True)

        # 创建队列
        self.queue = queue.Queue()

        # 开启线程
        threading.Thread(target=self.populate_treeview, daemon=True).start()
    
    def populate_treeview(self):
        for i, value in enumerate(self.default_values):
            max_emp_no = self.get_max_emp_no(value)
            # 将数据添加到队列中
            self.queue.put((i, value, max_emp_no))
        # 添加结束标记
        self.queue.put(None)

    def process_queue(self):
        try:
            while True:
                # 从队列中取出数据，插入到 Treeview 中
                item = self.queue.get_nowait()
                if item is None:
                    break
                i, value, max_emp_no = item
                self.tree.insert("", tk.END, values=(i, value, max_emp_no))
                self.queue.task_done()
        except queue.Empty:
            pass

        # 在 100 毫秒后再次调用 process_queue，以避免占用太多 CPU 资源
        self.master.after(100, self.process_queue)

    #获取人员编号
    def get_emp_no(self, pvalue0,limit=1,session=None):
        with requests.Session() as session:
            payloadSearch = {
                "combox0": "EmpNos0",
                "comboxCom0": "like",
                "pvalue0": pvalue0,
            }
            payload = {"start": 0, "limit": limit, "sort": "EmpNo", "dir": "DESC"}
            querystring = {"hqlQuery": "null"}
            headers = {
                "cookie": self.login_cookie,
                "Accept": "*/*",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Connection": "keep-alive",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Origin": "http://127.0.0.1",
                "Referer": "http://127.0.0.1/Frame/Index?SystemId=PF",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
                "X-Requested-With": "XMLHttpRequest",
                "Accept-Encoding": "deflate, gzip",
                "content-type": "application/x-www-form-urlencoded"
            }
            #筛选
            session.post(self.SEARCH_URL, data=payloadSearch, headers=headers)
            #实际获取数据
            response = session.post(self.GET_ALL_URL, data=payload, params=querystring, headers=headers)
            response.raise_for_status()
            response_str = response.text.replace('totalCount', '"totalCount"').replace('data', '"data"').replace('id', '"id"')
            response_str = json.loads(response_str)
            return response_str

    #获取最大编号
    def get_max_emp_no(self,pvalue0):
        #所有查询结果编号列表
        emp_no_list = []
        #最大值
        max_emp_no = 0
        #第一次查询结果
        first_response_str = self.get_emp_no(pvalue0)
        #获取总量
        total_count = first_response_str.get("totalCount")
        if(total_count == 0):
            return max_emp_no
        #获取具体数据
        emp_list = first_response_str.get("data")
        #判断编号是否获取完整
        if (total_count == len(emp_list)):
            max_emp_no = emp_list[0].get("EmpNo")
        else:
            all_response_str = self.get_emp_no(pvalue0,total_count)
            emp_list = all_response_str.get("data")
            # 获取所有以"pvalue0"开头的EmpNo
            emp_no_list = [item.get("EmpNo") for item in emp_list if item.get("EmpNo").startswith(str(pvalue0))]
            emp_no_list = natsort.natsorted(emp_no_list,reverse=True)
            max_emp_no = emp_no_list[0] if emp_no_list else max_emp_no
        return max_emp_no

    #获取最大编号并展示结果
    def get_max_emp_no_and_show_result(self):
            self.result_label.configure(text="查询中请等待！")
            pvalue0 = self.pvalue0_entry.get()
            max_emp_no = self.get_max_emp_no(pvalue0)
            self.result_label.configure(text="目前最大编号为：{}\n可设置的下一个编号为：{}".format(max_emp_no, self.increment_str(max_emp_no)))
            # self.result_label.configure(text=max_emp_no)

    #将程序加入线程中
    def fetch_max_emp_no(self):
        threading.Thread(target=self.get_max_emp_no_and_show_result).start()

    #获取默认查询编号
    def get_default_emp_no(self):
        year = str(datetime.datetime.now().year)
        year2 = year[2:]
        month = str(datetime.datetime.now().month)
        default_list = ["1"+year2, "4"+year2, "5"+year2,\
                       "7"+year2, "8"+year2, "9"+year2,
                       year+"530", year]
        if(month<"8"):
            default_list[-1]=int(year)-1
            default_list[-2]=f"{(int(year)-1)}530"
        return default_list

    def increment_str(self,emp_no):
        """将字符串分为数字和字母两个部分，分别处理后再合并为一个字符串。"""
        match = re.match(r"(\D*)(\d+)", emp_no)  # 匹配字符串
        if match is None:
            # 没有数字部分，直接返回原字符串
            return emp_no+"1"
        else:
            prefix, number = match.groups()
            # 数字部分加 1
            number = str(int(number) + 1)
            # 返回处理后的字符串
            return f"{prefix}{number}"

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.login_frame = LoginFrame(self)
        self.login_frame.pack()

if __name__ == "__main__":
    app = Application()
    app.mainloop()
