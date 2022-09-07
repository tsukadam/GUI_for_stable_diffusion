import tkinter as tk
from tkinter import scrolledtext
import subprocess
import configparser
import os
from concurrent.futures import ThreadPoolExecutor as threadPE
import queue

pathThis = os.path.dirname(__file__)
os.chdir(pathThis)

path_bat = "bat.bat"  # バッチファイル start.pyと同じディレクトリに入れる
path_log = "log.ini"  # ログファイル start.pyと同じディレクトリに入れる
path_setting = "setting.ini"  # 設定ファイル start.pyと同じディレクトリに入れる


# 引用符の削除
def delete_quote(oldText):
	newText = oldText.lstrip("\"")
	newText = newText.rstrip("\"")
	return newText


# 空白の削除
def delete_space(oldText):
	newText = oldText.lstrip(" ")
	return newText


class fileController:
	def __init__(self, mainGUI):
		self.mainGUI = mainGUI

	# 前回記録ファイルへ書き込み
	def write_log(self):
		pathFile = pathThis + "/" + path_log
		config = self.make_configPreData(pathFile)
		self.file_write(pathFile, config)

	def make_configPreData(self, pathFile):
		config = configparser.ConfigParser()
		config.read(pathFile, encoding="utf-8")

		promptText = self.mainGUI.input_prompt.get("1.0", "2.0")
		promptText = promptText.replace("\n", "")
		config["PRE"]["prompt"]     = promptText
		config["PRE"]["ddim_steps"] = self.mainGUI.input_ddim_steps.get()
		config["PRE"]["seed"]       = self.mainGUI.input_seed.get()
		config["PRE"]["n_iter"]     = self.mainGUI.input_n_iter.get()
		config["PRE"]["n_samples"]  = self.mainGUI.input_n_samples.get()
		config["PRE"]["H"]          = self.mainGUI.input_H.get()
		config["PRE"]["W"]          = self.mainGUI.input_W.get()
		config["PRE"]["init_img"]   = self.mainGUI.input_init_img.get()
		config["PRE"]["strength"]   = self.mainGUI.input_strength.get()
		config["PRE"]["tileable"]   = self.mainGUI.input_tileable.get()
		config["PRE"]["outdir"]     = self.mainGUI.input_outdir.get()
		return config

	def file_write(self, pathFile, config):
		with open(pathFile, "w") as file:
			config.write(file)

	# 前回記録ファイルの読み込み
	def read_log(self, orderData):
		config = configparser.ConfigParser()
		pathFile = pathThis + "/" + path_log
		if os.path.isfile(pathFile):
			config.read(pathFile, encoding="utf-8")
			orderData.prompt      = config["PRE"]["prompt"]
			orderData.ddim_steps  = config["PRE"]["ddim_steps"]
			orderData.seed        = config["PRE"]["seed"]
			orderData.n_iter      = config["PRE"]["n_iter"]
			orderData.n_samples   = config["PRE"]["n_samples"]
			orderData.H           = config["PRE"]["H"]
			orderData.W           = config["PRE"]["W"]
			orderData.init_img    = config["PRE"]["init_img"]
			orderData.strength    = config["PRE"]["strength"]
			orderData.tileable    = config["PRE"]["tileable"]
			orderData.outdir      = config["PRE"]["outdir"]

			orderData.prompt      = delete_quote(orderData.prompt)
			orderData.ddim_steps  = delete_quote(orderData.ddim_steps)
			orderData.seed        = delete_quote(orderData.seed)
			orderData.n_iter      = delete_quote(orderData.n_iter)
			orderData.n_samples   = delete_quote(orderData.n_samples)
			orderData.H           = delete_quote(orderData.H)
			orderData.W           = delete_quote(orderData.W)
			orderData.init_img    = delete_quote(orderData.init_img)
			orderData.strength    = delete_quote(orderData.strength)
			orderData.tileable    = delete_quote(orderData.tileable)
			orderData.outdir      = delete_quote(orderData.outdir)
		return orderData

	# 設定ファイルの読み込み
	def read_setting(self, pathData):
		config = configparser.ConfigParser()
		pathFile = pathThis + "/" + path_setting
		if os.path.isfile(pathFile):
			config.read(pathFile, encoding="utf-8")
			pathData.sdRoot             = config["PATH"]["sdRoot"]
			pathData.condaActivateBat   = config["PATH"]["condaActivateBat"]
			pathData.sdOptimizedTxt2img = config["PATH"]["sdOptimizedTxt2img"]
			pathData.sdOptimizedImg2img = config["PATH"]["sdOptimizedImg2img"]
			noQuoteSdRoot = delete_quote(pathData.sdRoot)
			pathData.sdRootDrive, _     = os.path.splitdrive(noQuoteSdRoot)
		else:
			pathData.sdRoot = "CantRead"
			pathData.sdRootDrive = "CantRead"
			pathData.condaActivateBat = "CantRead"
			pathData.sdOptimizedTxt2img = "CantRead"
			pathData.sdOptimizedImg2img = "CantRead"
		return pathData


class pathData:
	def __init__(self):
		self.sdRoot = "Init"
		self.sdRootDrive = "Init"
		self.condaActivateBat = "Init"
		self.sdOptimizedTxt2img = "Init"
		self.sdOptimizedImg2img = "Init"
		self.bat = path_bat

	def get_sdRoot(self):
		return self.sdRoot

	def get_sdRootDrive(self):
		return self.sdRootDrive

	def get_condaActivateBat(self):
		return self.condaActivateBat

	def get_sdOptimizedTxt2img(self):
		return self.sdOptimizedTxt2img

	def get_sdOptimizedImg2img(self):
		return self.sdOptimizedImg2img

	def get_bat(self):
		return self.bat


class orderData:
	def __init__(self):
		self.prompt      = "sample, test"
		self.ddim_steps  = "50"
		self.seed        = "10"
		self.n_iter      = "1"
		self.n_samples   = "5"
		self.H           = "512"
		self.W           = "512"
		self.init_img    = "Init"
		self.strength    = "0.7"
		self.tileable    = ""
		self.outdir      = ""

		self.cmd         = ""

		self.H_op1         = "64"
		self.H_op2         = "0"
		self.W_op1         = "64"
		self.W_op2         = "0"
		self.ddim_steps_op1         = "10"
		self.ddim_steps_op2         = "0"
		self.strength_op1         = "10"
		self.strength_op2         = "0"


	def set_prompt(self, value):
		self.prompt = value
	def set_ddim_steps(self, value):
		self.ddim_steps = value
	def set_seed(self, value):
		self.seed = value
	def set_n_iter(self, value):
		self.n_iter = value
	def set_n_samples(self, value):
		self.n_samples = value
	def set_H(self, value):
		self.H = value
	def set_W(self, value):
		self.W = value
	def set_init_img(self, value):
		self.init_img = value
	def set_strength(self, value):
		self.strength = value
	def set_tileable(self, value):
		self.tileable = value
	def set_outdir(self, value):
		self.outdir = value

	def set_H_op1(self, value):
		self.H_op1 = value
	def set_H_op2(self, value):
		self.H_op2 = value
	def set_W_op1(self, value):
		self.W_op1 = value
	def set_W_op2(self, value):
		self.W_op2 = value
	def set_ddim_steps_op1(self, value):
		self.ddim_steps_op1 = value
	def set_ddim_steps_op2(self, value):
		self.ddim_steps_op2 = value
	def set_strength_op1(self, value):
		self.strength_op1 = value
	def set_strength_op2(self, value):
		self.strength_op2 = value

	def get_prompt(self):
		return self.prompt
	def get_ddim_steps(self):
		return self.ddim_steps
	def get_seed(self):
		return self.seed
	def get_n_iter(self):
		return self.n_iter
	def get_n_samples(self):
		return self.n_samples
	def get_H(self):
		return self.H
	def get_W(self):
		return self.W
	def get_init_img(self):
		return self.init_img
	def get_strength(self):
		return self.strength
	def get_tileable(self):
		return self.tileable
	def get_outdir(self):
		return self.outdir

	def get_H_op1(self):
		return self.H_op1
	def get_H_op2(self):
		return self.H_op2
	def get_W_op1(self):
		return self.W_op1
	def get_W_op2(self):
		return self.W_op2
	def get_ddim_steps_op1(self):
		return self.ddim_steps_op1
	def get_ddim_steps_op2(self):
		return self.ddim_steps_op2
	def get_strength_op1(self):
		return self.strength_op1
	def get_strength_op2(self):
		return self.strength_op2


	def get_cmd(self):
		return self.cmd

	# コマンドにするための整形
	def make_cmd(self):
		cmd1 = "--prompt " + "\'" + self.prompt + "\'"
		cmd2 = " --ddim_steps " + self.ddim_steps
		cmd3 = " --seed " + self.seed
		cmd4 = " --n_iter " + self.n_iter
		cmd5 = " --n_samples " + self.n_samples
		cmd6 = " --H " + self.H
		cmd7 = " --W " + self.W
		cmd8 = " --init-img " + "\'" + self.init_img + "\'"
		cmd9 = " --strength " + self.strength
		cmd10 = "Init"

		# 保存先は入力がある時のみ使用
		if self.outdir == "":
			cmd11 = ""
		else:
			cmd11 = " --outdir " + self.outdir

		# tileableは入力がtileableの時のみ使用
		if self.tileable == "tileable":
			cmd10 = " --tileable"
		else:
			cmd10 = ""

		cmd = "Init"

		# imgかtxtかでコマンドの形を変える
		type = self.get_orderType()
		if type == "txt":
			cmd = cmd1+cmd2+cmd3+cmd4+cmd5+cmd6+cmd7+cmd10+cmd11
		else:
			cmd = cmd1+cmd2+cmd3+cmd4+cmd5+cmd6+cmd7+cmd8+cmd9+cmd10+cmd11
		cmd = " \"" + cmd + "\""
		self.cmd = cmd
		return cmd

	# imgかtxtかで実行ファイルのパスを返す
	def get_sdOptimized(self, pathData):
		type = self.get_orderType()
		if type == "txt":
			pathSdOpt = pathData.get_sdOptimizedTxt2img()
		else:
			pathSdOpt = pathData.get_sdOptimizedImg2img()
		return pathSdOpt

	# imgかtxtかを判定
	def get_orderType(self):
		if self.init_img == "Init" or self.init_img == "":
			return "txt"
		else:
			return "img"


class mainGUI(tk.Frame):
	def __init__(self, master=None):
		tk.Frame.__init__(self, master)

		# タイトルとウィンドウサイズの指定
		self.master.title("mainGUI")
		self.master.geometry("512x832")

		# 伸縮の指定
		self.master.columnconfigure(0, weight=1)
		self.master.rowconfigure(0, weight=1)
		self.columnconfigure(1, weight=1)
		self.columnconfigure(6, weight=1)

		self.create_widgets()

	def make_row(self, type, text, row, default, defaultOp):
		label1 = tk.Label(self, text=text, width=10)
		label1.grid(row=row, column=0, padx=5, pady=5, sticky=tk.E)

		if type == "basic" or type == "optional":
			input1 = tk.Entry(self, width=10)
			input1.insert(0, default)
			input1.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)
		elif type == "long":
			input1 = tk.Entry(self, width=20)
			input1.insert(0, default)
			input1.grid(row=row, column=1, columnspan=6, padx=5, pady=5, sticky=tk.W + tk.E)

		if type == "optional":
			label2 = tk.Label(self, text="から", width=5)
			label2.grid(row=row, column=2, padx=0, pady=5, sticky=tk.W)

			input2 = tk.Entry(self, width=5)
			input2.insert(0, defaultOp)
			input2.grid(row=row, column=3, padx=5, pady=5)

			label3 = tk.Label(self, text="刻みで", width=5)
			label3.grid(row=row, column=4, padx=0, pady=5, sticky=tk.W)

			input3 = tk.Entry(self, width=5)
			input3.insert(0, "0")
			input3.grid(row=row, column=5, padx=2, pady=5)

			label4 = tk.Label(self, text="種出力", width=5)
			label4.grid(row=row, column=6, padx=0, pady=5, sticky=tk.W)

			label5 = tk.Label(self, text="", width=5)  # 余白調整
			label5.grid(row=row, column=7, padx=2, pady=5)  # 余白調整

			return input1, input2, input3

		if type == "basic" or type == "long":
			return input1

	def create_widgets(self):
		label_prompt = tk.Label(self, text="prompt")
		label_prompt.grid(row=0, column=0, columnspan=8, padx=5, pady=5)

		self.input_prompt = scrolledtext.ScrolledText(self, wrap=tk.WORD, undo=True, width=80, height=10)
		self.input_prompt.insert("1.0", "a naked child loli, erotic, view of insect, F1.4, full colors")
		self.input_prompt.grid(row=1, column=0, columnspan=8, padx=5, pady=5)

		self.input_seed = self.make_row("basic", "seed", 2, "75", "defaultOp")
		self.input_n_iter = self.make_row("basic", "n_iter", 3, "1", "defaultOp")
		self.input_n_samples = self.make_row("basic", "n_samples", 4, "5", "defaultOp")
		self.input_H, self.input_H_op1, self.input_H_op2 = self.make_row("optional", "H", 5, "640", "64")
		self.input_W, self.input_W_op1, self.input_W_op2 = self.make_row("optional", "W", 6, "512", "64")
		self.input_ddim_steps, self.input_ddim_steps_op1, self.input_ddim_steps_op2 = self.make_row("optional", "ddim_steps", 7, "50", "10")
		self.input_init_img = self.make_row("long", "init_img", 8, "", "defaultOp")
		self.input_strength, self.input_strength_op1, self.input_strength_op2 = self.make_row("optional", "strength", 9, "0.5", "0.1")
		self.input_tileable = self.make_row("basic", "tileable", 10, "", "defaultOp")
		self.input_outdir = self.make_row("long", "outdir", 11, "D:\Desktop\AIImage\do_output", "defaultOp")

		self.run_button1 = tk.Button(self, text="Reload Setting.ini", width=20)
		self.run_button1.grid(row=12, column=0, columnspan=8, padx=5, pady=5)
		self.run_button2 = tk.Button(self, text="Output", width=20, command=lambda: myOutputController.do_output())
		self.run_button2.grid(row=13, column=0, columnspan=8, padx=5, pady=5)

		self.input_log = scrolledtext.ScrolledText(self, wrap=tk.NONE, undo=False, height = 10, bg="#eeeeee", fg="#000000", state='disabled')
		self.input_log.insert("1.0", "")
		self.input_log.grid(row=15, column=0, columnspan=8, padx=5, pady=5, sticky=tk.W + tk.E)

		self.run_button3 = tk.Button(self, text="Kill a waiting task", width=20, command=lambda: myQueueController.kill_qWaiting())
		self.run_button3.grid(row=16, column=0, columnspan=8, padx=5, pady=5)

	def delete_log(self):
		self.input_log.configure(state="normal")
		self.input_log.delete("1.0", "end")
		self.input_log.configure(state="disabled")

	def draw_log(self, position, text):
		self.input_log.configure(state="normal")
		self.input_log.insert(position, text)
		self.input_log.configure(state="disabled")


class inputController:
	def __init__(self, mainGUI, orderData):
		self.mainGUI = mainGUI
		self.orderData = orderData

	def set_orderToInput(self):
		self.mainGUI.input_ddim_steps.insert(0, self.orderData.get_ddim_steps())
		self.mainGUI.input_seed.insert(0, self.orderData.get_seed())
		self.mainGUI.input_n_iter.insert(0, self.orderData.get_n_iter())
		self.mainGUI.input_n_samples.insert(0, self.orderData.get_n_samples())
		self.mainGUI.input_H.insert(0, self.orderData.get_H())
		self.mainGUI.input_W.insert(0, self.orderData.get_W())
		self.mainGUI.input_init_img.insert(0, self.orderData.get_init_img())
		self.mainGUI.input_strength.insert(0, self.orderData.get_strength())
		self.mainGUI.input_tileable.insert(0, self.orderData.get_tileable())
		self.mainGUI.input_outdir.insert(0, self.orderData.get_outdir())

	def set_inputToOrder(self):
		promptText = self.mainGUI.input_prompt.get("1.0", "2.0")
		promptText = promptText.replace("\n", "")

		self.orderData.set_prompt(promptText)
		self.orderData.set_ddim_steps(self.mainGUI.input_ddim_steps.get())
		self.orderData.set_seed(self.mainGUI.input_seed.get())
		self.orderData.set_n_iter(self.mainGUI.input_n_iter.get())
		self.orderData.set_n_samples(self.mainGUI.input_n_samples.get())
		self.orderData.set_H(self.mainGUI.input_H.get())
		self.orderData.set_W(self.mainGUI.input_W.get())
		self.orderData.set_init_img(self.mainGUI.input_init_img.get())
		self.orderData.set_strength(self.mainGUI.input_strength.get())
		self.orderData.set_tileable(self.mainGUI.input_tileable.get())
		self.orderData.set_outdir(self.mainGUI.input_outdir.get())

		self.orderData.set_H_op1(self.mainGUI.input_H_op1.get())
		self.orderData.set_H_op2(self.mainGUI.input_H_op2.get())
		self.orderData.set_W_op1(self.mainGUI.input_W_op1.get())
		self.orderData.set_W_op2(self.mainGUI.input_W_op2.get())
		self.orderData.set_ddim_steps_op1(self.mainGUI.input_ddim_steps_op1.get())
		self.orderData.set_ddim_steps_op2(self.mainGUI.input_ddim_steps_op2.get())
		self.orderData.set_strength_op1(self.mainGUI.input_strength_op1.get())
		self.orderData.set_strength_op2(self.mainGUI.input_strength_op2.get())

		self.orderData.make_cmd()
		return self.orderData

	def set_H_inputToOrder(self):
		self.orderData.set_H(self.mainGUI.input_H.get())		
		return self.orderData

	def set_W_inputToOrder(self):
		self.orderData.set_W(self.mainGUI.input_W.get())		
		return self.orderData


	def delete_input(self):
		self.mainGUI.input_prompt.delete("1.0", "end")
		self.mainGUI.input_prompt.insert("1.0", preData.get_prompt())
		self.mainGUI.input_ddim_steps.delete(0, "end")
		self.mainGUI.input_seed.delete(0, "end")
		self.mainGUI.input_n_iter.delete(0, "end")
		self.mainGUI.input_n_samples.delete(0, "end")
		self.mainGUI.input_H.delete(0, "end")
		self.mainGUI.input_W.delete(0, "end")
		self.mainGUI.input_init_img.delete(0, "end")
		self.mainGUI.input_strength.delete(0, "end")
		self.mainGUI.input_tileable.delete(0, "end")
		self.mainGUI.input_outdir.delete(0, "end")


class queueController:
	def __init__(self, mainGUI, threadPE, pathData):
		self.qWaiting = queue.Queue()
		self.qProcessing = queue.Queue()
		self.qDone = queue.Queue()

		self.mainGUI = mainGUI
		self.threadPE = threadPE
		self.pathData = pathData

	def make_log(self):
		self.mainGUI.delete_log()
		for Data in self.qProcessing.queue:
			cmd = Data.get_cmd()
			cmd = delete_space(cmd)
			cmd = delete_quote(cmd)
			self.mainGUI.draw_log("1.0", "<Processing>" + cmd + "\n")
		for Data in self.qWaiting.queue:
			cmd = Data.get_cmd()
			cmd = delete_space(cmd)
			cmd = delete_quote(cmd)
			self.mainGUI.draw_log("end", "<Waiting>" + cmd + "\n")

	def push_qWaiting(self, orderData):
		self.qWaiting.put(orderData)
		if self.qProcessing.empty():
			self.push_qProcessing()
		self.make_log()

	def push_qProcessing(self):
		nowData = self.qWaiting.get()
		self.qProcessing.put(nowData)

		batController1 = batController(self.pathData, self.threadPE, self.mainGUI)
		future = self.threadPE.submit(batController1.do_bat, nowData)

		future.add_done_callback(self.push_qDone)
		self.make_log()

	def push_qDone(self, future):
		doneData = self.qProcessing.get()
		self.qDone.put(doneData)

		if not self.qWaiting.empty():
			self.push_qProcessing()
		self.make_log()

	def kill_qWaiting(self):
		if not self.qWaiting.empty():
			self.qWaiting.get()
		self.make_log()	


class batController:
	def __init__(self, pathData, threadPE, mainGUI):
		self.threadPE = threadPE
		self.pathData = pathData
		self.mainGUI = mainGUI

	def do_bat(self, orderData):
		pathBat = self.pathData.get_bat()
		cmd = orderData.get_cmd()
		pathSdRoot = self.pathData.get_sdRoot()

		pathSdRootDrive = self.pathData.get_sdRootDrive()
		pathConda = self.pathData.get_condaActivateBat()
		pathSdOpt = orderData.get_sdOptimized(self.pathData)

		print("call " + pathBat + " " + cmd + " " + pathSdRoot + 
			" " + pathSdRootDrive + " " + pathConda + " " + pathSdOpt)

		# バッチ実行
		subprocess.run(
			"call " + pathBat + " " + cmd + " " + pathSdRoot + 
			" " + pathSdRootDrive + " " + pathConda + " " + pathSdOpt,
			shell=True,
			encoding="shift-jis")


# 出力開始
class outputController:
	def __init__(self, inputController, queueController, fileController):
		self.inputController = inputController
		self.queueController = queueController
		self.fileController = fileController

	def do_output(self):
		myOrderData = self.inputController.set_inputToOrder()
		self.fileController.write_log()

		loop_H = int(myOrderData.get_H_op2())
		loop_W = int(myOrderData.get_W_op2())

		if loop_H > 1 or loop_W > 1:
			self.loop(myOrderData)
		else:
			self.queueController.push_qWaiting(myOrderData)

	def loop(self, myOrderData):

		myOrderData = self.inputController.set_H_inputToOrder()

		loop_H = int(myOrderData.get_H_op2())
		add_H = int(myOrderData.get_H_op1())
		num_H = int(myOrderData.get_H())
		if loop_H < 2:
			loop_H = 1

		for i in range(loop_H):
			myOrderData.set_H(str(num_H + (i * add_H)))

			myOrderData = self.inputController.set_W_inputToOrder()

			loop_W = int(myOrderData.get_W_op2())
			add_W = int(myOrderData.get_W_op1())
			num_W = int(myOrderData.get_W())
			if loop_W < 2:
				loop_W = 1

			for j in range(loop_W):
				myOrderData.set_W(str(num_W + (j * add_W)))



				self.queueController.push_qWaiting(myOrderData)



# ここから起動後処理
myThreadPE = threadPE(max_workers=1)
myMainGUI = mainGUI()
myMainGUI.grid()

myFileController = fileController(myMainGUI)

myPathData = pathData()
myPathData = myFileController.read_setting(myPathData)

myQueueController = queueController(myMainGUI, myThreadPE, myPathData)

preData = orderData()
preData = myFileController.read_log(preData)

myInputController = inputController(myMainGUI, preData)
myInputController.delete_input()
myInputController.set_orderToInput()

myOutputController = outputController(myInputController, myQueueController, myFileController)

# 	os.system('PAUSE')

# ウインドウ状態の維持
myMainGUI.mainloop()