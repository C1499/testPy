import tkinter as tk
from tkinter import ttk
import requests
import threading
import datetime
import natsort
import re
import json

class Application(tk.Frame):
    SEARCH_URL = "http://127.0.0.1/ViewHrmsEmp/SetSearch"
    GET_ALL_URL = "http://127.0.0.1/ViewHrmsEmp/GetAll"
    COOKIE = "td_cookie=3026703652; td_cookie=2448498669; ASP.NET_SessionId=swja5045cfabukbdjehoh455; CheckCode=9I7P"

    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("查询编号段最大值")
        self.pack()
        self.default_values = self.get_default_emp_no()
        self.create_widgets()

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

        # Populate Treeview with sample data
        for i, value in enumerate(self.default_values):
            with requests.Session() as session:
                self.tree.insert("", tk.END, values=(i,value, self.get_max_emp_no(value)))

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
                "cookie": self.COOKIE,
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
        #临时卡[1+年份末两位……]、教工子女卡[4+年份末两位……]、初中物业卡[5+年份末两位……]、高中物业卡[7+年份末两位……]、高中教师卡[8+年份末两位……]、初中教工卡[9+年份末两位……]
        #高中部学生卡[年份四位+530]、初中学生卡[年份四位+班级两位……]
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
root = tk.Tk()
app = Application(master=root)
app.mainloop()