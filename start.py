import tkinter as tk
from tkinter import scrolledtext
from tkinter import filedialog
import tkinter.ttk as ttk
import subprocess
import configparser
import os
from concurrent.futures import ThreadPoolExecutor as threadPE
import queue
import re

import datetime
t_delta = datetime.timedelta(hours=9)
JST = datetime.timezone(t_delta, 'JST')

thisPath = os.path.dirname(__file__)
os.chdir(thisPath)

batPath = "bat.bat"  # バッチファイル start.pyと同じディレクトリに入れる
logPath = "log.ini"  # ログファイル start.pyと同じディレクトリに入れる
settingPath = "setting.ini"  # 設定ファイル start.pyと同じディレクトリに入れる


def delete_quote(oldText):  # 引用符の削除
        newText = oldText.replace("\"","")
        return newText

def delete_space(oldText):  # 空白の削除
        newText = oldText.lstrip(" ")
        return newText

# 指示項目の名前リスト
itemNameList = ["prompt", "ddim_steps", "seed", "n_iter", "n_samples", "H", "W", "init_img", "strength", "tileable", "outdir", "plms", "scale"]
# 指示項目レイヤーの名前リスト
# taskDataはMAINを一次元辞書で持ち、orderDataは他のレイヤーも二次元辞書で持つ
itemLayerNameList = ["MAIN", "OP1", "OP2"]

# 設定項目の名前リスト
settingNameList = ["sdRoot", "condaActivateBat", "sdOptimizedTxt2img", "sdOptimizedImg2img"]
# 設定項目レイヤーの名前リスト
settingLayerNameList = ["PATH"]
# デフォルトの実行ファイル場所（sdRoot基準）
defaultTxt2imgPath = "optimizedSD/optimized_txt2img.py"
defaultImg2imgPath = "optimizedSD/optimized_img2img.py"


def itemList(itemLayerNameList, itemNameList):  # 名前リストを渡すと辞書を返す
        itemList = {}
        for layer in itemLayerNameList:
                itemList[layer] = {}
                for itemName in itemNameList:
                        itemList[layer].update({itemName : ""})
        return itemList

        
class fileController:
        def __init__(self):
                pass

        def check_existAndPerfectIni(self, filePath, itemList):
        # iniファイルがない場合、Falseを返す iniファイルのキーがリストと合わない場合、Falseを返す
                if os.path.isfile(filePath):
                        count = 0
                        config = configparser.ConfigParser()
                        config.read(filePath, encoding="shift_jis")
                        for layer in itemList:
                                for name in itemList[layer]:
                                        try:
                                                if config.get(layer, name) == None:
                                                        count += 1
                                        except:
                                                count += 1
                        if count == 0:
                                return True
                        else:
                                return False
                else:
                        return False

        def make_ini(self, itemList, filePath):  # iniを生成する
                config = configparser.ConfigParser()
                for layer in itemList:
                        try:
                                config.add_section(layer)
                        except configparser.DuplicateSectionError:
                                print("configparser.DuplicateSectionError in make_log")
                                pass
                        for itemName in itemList[layer]:
                                config.set(layer, itemName, itemList[layer][itemName])
                with open(filePath, "w") as file:
                        config.write(file)
                print(filePath + "を生成した")


        def read_ini(self, filePath, itemList):  # iniファイルを読み込んで、渡したitemListと同じスタイルのitemListを返す
                if not os.path.isfile(filePath):  # iniがない場合、もらったリストを返して処理中断する
                        print("iniがない")
                        return itemList
                else:
                        
                        if not self.check_existAndPerfectIni(filePath, itemList): #itemListの形式が合わない場合、もらったリストを返して処理中断する
                                print("指定されたitemListとiniの形式が合わない")
                                return itemList
                        else:
                                config = configparser.ConfigParser()
                                config.read(filePath, encoding="shift_jis")
                                for layer in itemList:
                                        for itemName in itemList[layer]:
                                                value = config.get(layer, itemName)
                                                value = delete_quote(value)
                                                itemList[layer][itemName] = value
                                itemList = self.back_blank(itemList)
                                return itemList

        def write_ini(self, filePath, itemList):  # itemListを受け取ってiniに書き込む              
                if not os.path.isfile(filePath):  # iniがない場合生成する
                        self.make_ini(itemList, filePath)
                elif not self.check_existAndPerfectIni(filePath, itemList): # iniが不完全な場合、削除してから生成する
                        os.remove(filePath)
                        self.make_ini(itemList, filePath)
                        
                config = configparser.ConfigParser()
                config.read(filePath, encoding="shift_jis")
                itemList = self.replace_blank(itemList)
                for layer in itemList:
                        for itemName in itemList[layer]:
                                try:
                                        config[layer][itemName] = itemList[layer][itemName]
                                except KeyError:
                                        print("KeyError in write_ini")
                                        pass
                with open(filePath, "w") as file:
                        config.write(file)

                itemList = self.back_blank(itemList)

        def replace_blank(self, itemList):
                for layer in itemList:
                        for itemName in itemList[layer]:
                                if itemList[layer][itemName] == "":
                                        itemList[layer][itemName] = "##BLANK##"  # 空文字はNoneになってしまうため、置き換える               
                return itemList

        def back_blank(self, itemList):
                for layer in itemList:
                        for itemName in itemList[layer]:
                                if itemList[layer][itemName] == "##BLANK##":
                                        itemList[layer][itemName] = ""  # 置き換えた空文字を戻す                
                return itemList
        
        def set_log(self, itemList):  # itemListを受け取って前回ログに書き込む
                filePath = thisPath + "/" + logPath                
                self.write_ini(filePath, itemList)

        def get_log(self):  # 前回ログから読み込んでitemListを返す
                filePath = thisPath + "/" + logPath
                myItemList = itemList(itemLayerNameList, itemNameList)                
                resultList = self.read_ini(filePath, myItemList)
                return resultList

        def set_setting(self, itemList):  # itemListを受け取って設定ファイルに書き込む
                filePath = thisPath + "/" + settingPath
                self.write_ini(filePath, itemList)

        def get_setting(self):  # 設定ファイルを読み込んでitemListを返す        
                filePath = thisPath + "/" + settingPath
                settingList = itemList(settingLayerNameList, settingNameList)
                resultList = self.read_ini(filePath, settingList)
                return resultList
        
        def check_setting(self):  # 設定ファイルの存在と内容を確認し、True/Falseを返す
                filePath = thisPath + "/" + settingPath
                settingList = itemList(settingLayerNameList, settingNameList)
                if self.check_existAndPerfectIni(filePath, settingList):
                        return True
                else:
                        return False


class pathData:
        def __init__(self, fileController):
                self.pathList = itemList(settingLayerNameList, settingNameList)
                self.fileController = fileController
                self.get_pathFromSetting()

        def get_pathFromSetting(self):
                self.pathList = self.fileController.get_setting()
                
        def set(self, itemName, layer, value):
                self.pathList[layer][itemName] = value

        def get(self, itemName, layer):
                return self.pathList[layer][itemName]
        
        def get_sdRootDrive(self):
                sdRootPath = self.get("sdRoot","PATH")
                sdRootPath = delete_quote(sdRootPath)
                sdRootDrivePath, _     = os.path.splitdrive(sdRootPath)
                return sdRootDrivePath


class orderData:
        def __init__(self):
                self.itemList = itemList(itemLayerNameList, itemNameList)
                self.variant = {}

        def set_itemList(self, itemList):
                self.itemList = itemList

        def set_variant(self, variant):
                self.variant = variant
                
        def set(self, itemName, layer, value):
                self.itemList[layer][itemName] = value

        def get(self, itemName, layer):
                return self.itemList[layer][itemName]
        
        def get_itemList(self):
                return self.itemList

        def get_variant(self):
                return self.variant

        def get_optionInfo(self):
                optionInfo = {}
                for itemName in itemNameList:
                        if not self.get(itemName, "OP2") == "":
                                OP1 = self.get(itemName, "OP1")
                                OP2 = self.get(itemName, "OP2")
                                try:
                                        OP1 = float(OP1)
                                except(TypeError, ValueError):
                                        OP1 = float(0)
                                try:
                                        OP2 = int(OP2)
                                except(TypeError, ValueError):
                                        OP2 = int(0)

                                if OP2 < 2 or OP1 == 0:  # 意味のない入力の時は含めない
                                        pass
                                else:
                                        optionInfo[itemName] = {"OP1" : OP1, "OP2" : OP2}
                return optionInfo


class taskData:
        def __init__(self):
                self.itemList = {}
                for itemName in itemNameList:
                        self.itemList[itemName] = ""
                self.cmd = ""
                
        def set(self, itemName, value):
                self.itemList[itemName] = value

        def get(self, itemName):
                return self.itemList[itemName]

        def get_itemList(self):
                return self.itemList        
       
        def make_cmd(self):   # バッチに渡すコマンドを生成
                cmd = []
                for i in range(13):
                        cmd.append("")
                
                if not self.get("prompt") == "":
                        cmd[0] = "--prompt " + "\'" + self.get("prompt") + "\'"
                else:
                        cmd[0] = "--prompt " + "\'" + "No prompt" + "\'"  # promptは、ないとスペースが崩れるので入れる
                if not self.get("ddim_steps") == "":
                        cmd[1] = " --ddim_steps " + self.get("ddim_steps")
                if not self.get("seed") == "":
                        cmd[2] = " --seed " + self.get("seed")
                if not self.get("n_iter") == "":
                        cmd[3] = " --n_iter " + self.get("n_iter")
                if not self.get("n_samples") == "":
                        cmd[4] = " --n_samples " + self.get("n_samples")
                if not self.get("H") == "":
                        cmd[5] = " --H " + self.get("H")
                if not self.get("W") == "":
                        cmd[6] = " --W " + self.get("W")
                if not self.get("init_img") == "":
                        cmd[7] = " --init-img " + "\'" + self.get("init_img") + "\'"
                if not self.get("strength") == "":
                        cmd[8] = " --strength " + self.get("strength")
                # tileableは入力がtileableの時のみ使用
                if self.get("tileable") == "tileable":
                        cmd[9] = " --tileable"
                if not self.get("outdir") == "":
                        cmd[10] = " --outdir " + self.get("outdir")
                if not self.get("plms") == "":
                        cmd[11] = " --plms"
                if not self.get("scale") == "":
                        cmd[12] = " --scale " + self.get("scale")

                # imgかtxtかでコマンドの形を変える
                mode = self.get_mode()
                if mode == "txt":
                        cmd = cmd[0]+cmd[1]+cmd[2]+cmd[3]+cmd[4]+cmd[5]+cmd[6]+cmd[9]+cmd[10]+cmd[11]+cmd[12]
                else:
                        cmd = cmd[0]+cmd[1]+cmd[2]+cmd[3]+cmd[4]+cmd[5]+cmd[6]+cmd[7]+cmd[8]+cmd[9]+cmd[10]+cmd[11]+cmd[12]
                cmd = " \"" + cmd + "\""
                self.cmd = cmd
                return cmd

        def get_cmd(self):
                if self.cmd == "":
                        self.make_cmd()
                return self.cmd

        def get_execute(self, pathData):  # imgかtxtで実行ファイルのパスを返す
                mode = self.get_mode()                
                if mode == "txt":
                        path = pathData.get("sdOptimizedTxt2img", "PATH")
                else:
                        path = pathData.get("sdOptimizedImg2img", "PATH")
                return path
        
        def get_mode(self):  # init_imgがあるかないかでimgかtxtかを判定し、文字列imgかtxtを返す
                if self.get("init_img") == "":
                        return "txt"
                else:
                        return "img"


class mainGUI(tk.Frame):
        def __init__(self, master=None):
                tk.Frame.__init__(self, master)
                self.pack(fill=tk.BOTH, expand=tk.YES)

                # メインウインドウ
                self.master.title("GUI for stable diffusion")
                self.master.geometry("512x832")
                self.master.minsize(448, 832)

                self.master.columnconfigure(0, weight=1)
                self.columnconfigure(1, weight=1)
                self.columnconfigure(6, weight=1)

                self.create_widgets()

        def make_settingvar(self):
                var1 = tk.StringVar()
                var1.set("")
                return var1

        def make_setting(self, target, mode, text, row, default, var):
                label1 = tk.Label(target, text=text, width=30)
                label1.grid(row=row, column=0, padx=5, pady=3, sticky=tk.E)
                
                if mode == "settingdir":
                        input1 = tk.Entry(target, width=30, textvariable=var)
                        input1.grid(row=row, column=1, columnspan=5, padx=5, pady=3, sticky=tk.W + tk.E)
                        
                        button1 = tk.Button(target, text="Browse..", width=10, command=lambda: myInputController.set_settingDir(var))
                        button1.grid(row=row, column=6, columnspan=1, padx=5, pady=3, sticky=tk.W)
                elif mode == "settingfile":
                        input1 = tk.Entry(target, width=30, textvariable=var)
                        input1.grid(row=row, column=1, columnspan=5, padx=5, pady=3, sticky=tk.W + tk.E)
                        
                        button1 = tk.Button(target, text="Browse..", width=10, command=lambda: myInputController.set_settingFile(var))
                        button1.grid(row=row, column=6, columnspan=1, padx=5, pady=3, sticky=tk.W)
                
        
        def make_main(self, target, mode, text, row, default):
                label1 = tk.Label(target, text=text, width=10)
                label1.grid(row=row, column=0, padx=5, pady=3, sticky=tk.E)

                var1 = tk.StringVar()
                var1.set(default)

                if mode == "basic" or mode == "optional":
                        input1 = tk.Entry(target, width=10, textvariable=var1)
                        input1.grid(row=row, column=1, padx=5, pady=3, sticky=tk.W + tk.E)
                elif mode == "long":
                        input1 = tk.Entry(target, width=15, textvariable=var1)
                        input1.grid(row=row, column=1, columnspan=6, padx=5, pady=3, sticky=tk.W + tk.E)
                elif mode == "check":
                        var1 = tk.BooleanVar()
                        var1.set(False)
                        input1 = tk.Checkbutton(target, variable=var1)
                        input1.grid(row=row, column=1, columnspan=6, padx=0, pady=0, sticky=tk.W)                        
                elif mode == "dir":
                        input1 = tk.Entry(target, width=15, textvariable=var1)
                        input1.grid(row=row, column=1, columnspan=5, padx=5, pady=3, sticky=tk.W + tk.E)
                        
                        button1 = tk.Button(target, text="Browse..", width=10, command=lambda: myInputController.set_outdir())
                        button1.grid(row=row, column=6, columnspan=1, padx=5, pady=3, sticky=tk.W)                        
                elif mode == "file":
                        input1 = tk.Entry(target, width=15, textvariable=var1)
                        input1.grid(row=row, column=1, columnspan=5, padx=5, pady=3, sticky=tk.W + tk.E)
                        
                        button1 = tk.Button(target, text="Browse..", width=10, command=lambda: myInputController.set_init_img())
                        button1.grid(row=row, column=6, columnspan=1, padx=5, pady=3, sticky=tk.W)

                return var1

        def make_op1(self, target, row, default):
                var1 = tk.StringVar()
                var1.set(default)

                label2 = tk.Label(target, text="から", width=5)
                label2.grid(row=row, column=2, padx=0, pady=3, sticky=tk.W)

                input2 = tk.Entry(target, width=5, textvariable=var1)
                input2.grid(row=row, column=3, padx=5, pady=3)

                label3 = tk.Label(target, text="刻みで", width=5)
                label3.grid(row=row, column=4, padx=0, pady=3, sticky=tk.W)

                return var1

        def make_op2(self, target, row, default):
                var1 = tk.StringVar()
                var1.set(default)

                input3 = tk.Entry(target, width=5, textvariable=var1)
                input3.grid(row=row, column=5, padx=2, pady=3)

                label4 = tk.Label(target, text="種出力", width=5)
                label4.grid(row=row, column=6, padx=0, pady=3, sticky=tk.W)

                return var1

        def create_widgets(self):               
                label_prompt = tk.Label(self, text="prompt")
                label_prompt.grid(row=0, column=0, columnspan=7, padx=5, pady=3, sticky=tk.W + tk.E)

                self.input_prompt = scrolledtext.ScrolledText(self, wrap=tk.CHAR, undo=True, width=500, height=9)
                self.input_prompt.insert("1.0", "sample, test")
                self.input_prompt.grid(row=1, column=0, columnspan=7, padx=5, pady=3, sticky=tk.W + tk.E)

                self.var_seed = self.make_main(self, "basic", "seed", 2, "75")
                self.var_n_iter = self.make_main(self, "basic", "n_iter", 3, "1")
                self.var_n_samples = self.make_main(self, "basic", "n_samples", 4, "5")
                self.var_H =self.make_main(self, "optional", "H", 5, "640")
                self.var_W = self.make_main(self, "optional", "W", 6, "512")
                self.var_ddim_steps = self.make_main(self, "optional", "ddim_steps", 7, "50")
                self.var_scale = self.make_main(self, "optional", "scale", 8, "7.5")
                self.var_tileable = self.make_main(self, "check", "tileable", 9, "")
#                self.var_plms = self.make_main(self, "check", "plms", 10, "")  # optimizedにないオプション
                self.var_outdir = self.make_main(self, "dir", "outdir", 10, "")

                self.var_H_op1= self.make_op1(self, 5, "64")
                self.var_H_op2 = self.make_op2(self, 5, "1")
                self.var_W_op1 = self.make_op1(self, 6, "64")
                self.var_W_op2 = self.make_op2(self, 6, "1")
                self.var_ddim_steps_op1 = self.make_op1(self, 7, "10")
                self.var_ddim_steps_op2 = self.make_op2(self, 7, "1")
                self.var_strength_op1 = self.make_op1(self, 13, "0.1")
                self.var_strength_op2 = self.make_op2(self, 13, "1")
                self.var_scale_op1 = self.make_op1(self, 8, "2")
                self.var_scale_op2 = self.make_op2(self, 8, "1")
                
                self.sep1 = ttk.Separator(self, orient="horizontal")
                self.sep1.grid(row=11, column=0, columnspan=7, padx=20, pady=20, sticky=tk.W + tk.E)
                
                self.var_init_img = self.make_main(self, "file", "init_img", 12, "")
                self.var_strength = self.make_main(self, "optional", "strength", 13, "0.5")

                self.sep2 = ttk.Separator(self, orient="horizontal")
                self.sep2.grid(row=14, column=0, columnspan=7, padx=20, pady=20, sticky=tk.W + tk.E)

                self.run_button2 = tk.Button(self, text="Output", width=20, command=lambda: myOutputController.do_output())
                self.run_button2.grid(row=15, column=0, columnspan=7, padx=5, pady=3)

                self.countText = tk.StringVar()
                self.countText.set("出力枚数：")
                label_count = tk.Label(self, textvariable=self.countText)
                label_count.grid(row=16, column=0, columnspan=7, padx=5, pady=3, sticky=tk.W + tk.E)

                self.input_qBox = scrolledtext.ScrolledText(self, wrap=tk.NONE, undo=False, width=500, height = 9, bg="#eeeeee", fg="#000000", state='disabled')
                self.input_qBox.insert("1.0", "")
                self.input_qBox.grid(row=17, column=0, columnspan=7, padx=5, pady=3, sticky=tk.W + tk.E)

                self.run_button3 = tk.Button(self, text="Kill a task", width=15, command=lambda: myQueueController.kill_qWaiting())
                self.run_button3.grid(row=18, column=5, columnspan=3, padx=10, pady=3, sticky=tk.E)

                self.run_button4 = tk.Button(self, text="Kill all", width=15, command=lambda: myQueueController.allkill_qWaiting())
                self.run_button4.grid(row=19, column=5, columnspan=3, padx=10, pady=3, sticky=tk.E)

                self.run_button1 = tk.Button(self, text="Setting", width=15, command=lambda: myInputController.prepare_settingDlg())
                self.run_button1.grid(row=19, column=0, columnspan=3, padx=5, pady=3, sticky=tk.W)

                self.var_n_iter.trace_add("write", self.draw_number)
                self.var_n_samples.trace_add("write", self.draw_number)

                self.var_H_op2.trace_add("write", self.draw_number)
                self.var_W_op2.trace_add("write", self.draw_number)
                self.var_ddim_steps_op2.trace_add("write", self.draw_number)
                self.var_strength_op2.trace_add("write", self.draw_number)
                self.var_scale_op2.trace_add("write", self.draw_number)
                self.var_init_img.trace_add("write", self.draw_number)
 

                self.var_sdRoot = self.make_settingvar()
                self.var_condaActivateBat = self.make_settingvar()
                self.var_sdOptimizedTxt2img = self.make_settingvar()
                self.var_sdOptimizedImg2img = self.make_settingvar()

        def open_settingDlg(self):   # 設定ダイアログ
                dlg_modal = tk.Toplevel(self)
                
                dlg_modal.title("Setting Dialog")
                dlg_modal.geometry("512x224")
                dlg_modal.resizable(width=False, height=False)

                dlg_modal.columnconfigure(0, weight=1)
                dlg_modal.columnconfigure(1, weight=3)
                dlg_modal.columnconfigure(6, weight=1)

                dlg_modal.grab_set()
                dlg_modal.focus_set()
                dlg_modal.transient(self.master)

                label_setting = tk.Label(dlg_modal, text="パスを設定してください")
                label_setting.grid(row=0, column=0, columnspan=7, padx=5, pady=3, sticky=tk.W + tk.E)

                self.make_setting(dlg_modal, "settingdir", "stable-diffusionのルートフォルダ", 1, "", self.var_sdRoot)
                self.make_setting(dlg_modal, "settingfile", "anaconda3をアクティベートする.batファイル", 2, "", self.var_condaActivateBat)
                self.make_setting(dlg_modal, "settingfile", "txt2imgの実行ファイル", 3, "", self.var_sdOptimizedTxt2img)
                self.make_setting(dlg_modal, "settingfile", "img2imgの実行ファイル", 4, "", self.var_sdOptimizedImg2img)

                run_buttonSetting = tk.Button(dlg_modal, text="OK", width=15, command=lambda: myInputController.do_setting(dlg_modal))
                run_buttonSetting.grid(row=5, column=0, columnspan=7, padx=5, pady=20)

                self.master.wait_window(dlg_modal)

        def open_dlg(self, text):  # 汎用ダイアログ
                dlg = tk.Toplevel(self)
                
                dlg.title("Dialog")
                dlg.geometry("384x128")
                dlg.resizable(width=False, height=False)

                dlg.columnconfigure(0, weight=1)
                dlg.rowconfigure(0, weight=1)
                dlg.rowconfigure(1, weight=1)

                dlg.grab_set()
                dlg.focus_set()
                dlg.transient(self.master)

                label_dlg = tk.Label(dlg, text=text)
                label_dlg.grid(row=0, column=0, padx=5, pady=3, sticky=tk.W + tk.E)

                run_buttonSetting = tk.Button(dlg, text="OK", width=15, command=dlg.destroy)
                run_buttonSetting.grid(row=1, column=0, padx=5, pady=10)
                self.master.wait_window(dlg)
                                
        def draw_number(self, a, b, c):
                num=[]
                num.append(self.var_n_iter.get())
                num.append(self.var_n_samples.get())
                num.append(self.var_H_op2.get())
                num.append(self.var_W_op2.get())
                num.append(self.var_ddim_steps_op2.get())
                num.append(self.var_scale_op2.get())

                if not self.var_init_img.get() == "":
                        num.append(self.var_strength_op2.get())
                        
                num_all = 1
                for n in num:
                        if n:
                                try:
                                        n = int(n)
                                        if n == 0:
                                                n = 1
                                        num_all *= n
                                except:
                                        pass

                self.countText.set("出力枚数：" + str(num_all))


class inputController:
        def __init__(self, mainGUI, fileController):
                self.mainGUI = mainGUI
                self.inputList = self.make_inputList()
                self.settingList = self.make_settingList()
                self.input_qBox = mainGUI.input_qBox
                self.fileController = fileController
                
        def make_inputList(self):
                myList = itemList(itemLayerNameList, itemNameList)

                myList["MAIN"]["prompt"] = self.mainGUI.input_prompt
                myList["MAIN"]["seed"] = self.mainGUI.var_seed
                myList["MAIN"]["n_iter"] = self.mainGUI.var_n_iter
                myList["MAIN"]["n_samples"] = self.mainGUI.var_n_samples
                myList["MAIN"]["H"] = self.mainGUI.var_H
                myList["MAIN"]["W"] = self.mainGUI.var_W
                myList["MAIN"]["ddim_steps"] = self.mainGUI.var_ddim_steps
                myList["MAIN"]["init_img"] = self.mainGUI.var_init_img
                myList["MAIN"]["strength"] = self.mainGUI.var_strength
                myList["MAIN"]["tileable"] = self.mainGUI.var_tileable
                myList["MAIN"]["outdir"] = self.mainGUI.var_outdir
#                myList["MAIN"]["plms"] = self.mainGUI.var_plms  # optimizedにないオプション
                myList["MAIN"]["scale"] = self.mainGUI.var_scale

                myList["OP1"]["H"] = self.mainGUI.var_H_op1
                myList["OP1"]["W"] = self.mainGUI.var_W_op1
                myList["OP1"]["ddim_steps"] = self.mainGUI.var_ddim_steps_op1
                myList["OP1"]["strength"] = self.mainGUI.var_strength_op1
                myList["OP1"]["scale"] = self.mainGUI.var_scale_op1

                myList["OP2"]["H"] = self.mainGUI.var_H_op2
                myList["OP2"]["W"] = self.mainGUI.var_W_op2
                myList["OP2"]["ddim_steps"] = self.mainGUI.var_ddim_steps_op2
                myList["OP2"]["strength"] = self.mainGUI.var_strength_op2
                myList["OP2"]["scale"] = self.mainGUI.var_scale_op2

                return myList

        def make_settingList(self):
                myList = itemList(settingLayerNameList, settingNameList)
                myList["PATH"]["sdRoot"] = self.mainGUI.var_sdRoot
                myList["PATH"]["condaActivateBat"] = self.mainGUI.var_condaActivateBat
                myList["PATH"]["sdOptimizedTxt2img"] = self.mainGUI.var_sdOptimizedTxt2img
                myList["PATH"]["sdOptimizedImg2img"] = self.mainGUI.var_sdOptimizedImg2img
                
                self.mainGUI.var_sdRoot.trace_add("write", self.set_InputToSettingFile_trace)
                self.mainGUI.var_condaActivateBat.trace_add("write", self.set_InputToSettingFile_trace)
                self.mainGUI.var_sdOptimizedTxt2img.trace_add("write", self.set_InputToSettingFile_trace)
                self.mainGUI.var_sdOptimizedImg2img.trace_add("write", self.set_InputToSettingFile_trace)

                return myList

        def check_setting(self):  # iniを読んでから、設定に欠けがあるか確認
                self.set_settingFileToInput()

                myList = self.get_inputToSettingList()
                blank = 0
                for layer in myList:
                        for itemName in myList[layer]:
                                if myList[layer][itemName]=="":
                                        blank +=1
                if blank > 0:
                        return False
                else:
                        return True

        def set_defaultPath(self):  # 実行ファイルが空欄の時、デフォルトの設定を入れる
                check = 0
                if not self.mainGUI.var_sdOptimizedTxt2img.get():
                        self.mainGUI.var_sdOptimizedTxt2img.set(defaultTxt2imgPath)
                        check += 1
                if not self.mainGUI.var_sdOptimizedImg2img.get():
                        self.mainGUI.var_sdOptimizedImg2img.set(defaultImg2imgPath)
                        check += 1
                if check >= 1:
                        self.mainGUI.open_dlg("デフォルトの実行ファイルを設定しました")

                return check

        def set_settingFileToInput(self):  # 設定iniの内容を入力欄に書き込む
                myList = self.fileController.get_setting()
                self.set_settingListToInput(myList)

        def set_InputToSettingFile(self):  # 入力欄の内容を設定iniに書き込む
                myList = self.get_inputToSettingList()
                self.fileController.set_setting(myList)

        def set_InputToSettingFile_trace(self, a, b, c):  # 上記をtrace_addから呼び出す時用
                self.set_InputToSettingFile()

        def prepare_settingDlg(self):  # 設定ダイアログを開く直前の処理
                self.set_settingFileToInput()
                self.set_defaultPath()
                self.mainGUI.open_settingDlg()

        def do_setting(self, dlg):
                if not self.check_setting():                        
                        self.mainGUI.open_dlg("空欄があると動作しません")
                        self.set_defaultPath()
                        if self.check_setting():
                                dlg.destroy()
                else:
                        dlg.destroy()

        def set_settingDir(self, var):
                path = tk.filedialog.askdirectory(title="Select a folder")
                if not path == None and not path == "":
                        var.set(path)

        def set_settingFile(self, var):
                path = tk.filedialog.askopenfilename(title="Select a file", multiple=False)
                if not path == None and not path == "":
                        var.set(path)

        def set_outdir(self):
                path = tk.filedialog.askdirectory(title="Select a folder")
                if not path == None and not path == "":
                        self.set("outdir", "MAIN", path)

        def set_init_img(self):
                path = tk.filedialog.askopenfilename(title="Select a file", multiple=False)
                if not path == None and not path == "":
                        self.set("init_img", "MAIN", path)

        def set_setting(self, itemName, value):
                self.settingList["PATH"][itemName].set(value)

        def get_setting(self, itemName):
               return self.settingList["PATH"][itemName].get()
                
        def set(self, itemName, layer, value):
                self.delete(itemName, layer)
                if not self.inputList[layer][itemName] == "":  # 文字列はsetで操作できないため                        
                        if layer == "MAIN":
                                if itemName == "prompt":
                                        self.inputList[layer][itemName].insert("1.0", value)
                                elif itemName == "tileable":
                                        if self.inputList[layer][itemName].get == "tileable":
                                                self.inputList[layer][itemName].set(True)
                                        else :
                                                self.inputList[layer][itemName].set(False)
                                elif itemName == "plms":
                                        if self.inputList[layer][itemName].get == "plms":
                                                self.inputList[layer][itemName].set(True)
                                        else :
                                                self.inputList[layer][itemName].set(False)
                                else:
                                        self.inputList[layer][itemName].set(value)                                        
                        else:
                                self.inputList[layer][itemName].set(value)

        def get(self, itemName, layer):
                if not self.inputList[layer][itemName] == "":  # 文字列はsetで操作できないため
                        if layer == "MAIN":                                
                                if itemName == "prompt":
                                        text = self.inputList[layer][itemName].get("1.0", "2.0")
                                        text = text.replace("\n", "")
                                        return text
                                elif itemName == "tileable":
                                        if self.inputList[layer][itemName].get() == True:
                                                text = "tileable"
                                        else:
                                                text = ""
                                        return text
                                elif itemName == "plms":
                                        if self.inputList[layer][itemName].get() == True:
                                                text = "plms"
                                        else:
                                                text = ""
                                        return text
                                else:
                                        return self.inputList[layer][itemName].get()
                        else:
                                return self.inputList[layer][itemName].get()
                else:
                        return ""

        def delete(self, itemName, layer):
                if not self.inputList[layer][itemName] == "":  # 文字列はsetで操作できないため
                        if itemName == "prompt" and layer == "MAIN":
                                self.inputList[layer][itemName].delete("1.0", "end")
                        elif itemName == "tileable" and layer == "MAIN":                                
                                self.inputList[layer][itemName].set(False)
                        elif itemName == "plms" and layer == "MAIN":
                                self.inputList[layer][itemName].set(False)
                        else:
                                self.inputList[layer][itemName].set("")

        def delete_qBox(self):
                self.input_qBox.configure(state = "normal")
                self.input_qBox.delete("1.0", "end")
                self.input_qBox.configure(state = "disabled")

        def set_qBox(self, position, text):
                self.input_qBox.configure(state = "normal")
                self.input_qBox.insert(position, text)
                self.input_qBox.configure(state = "disabled")
                                
        def get_inputToItemList(self):
                myList = itemList(itemLayerNameList, itemNameList)
                for layer in itemLayerNameList:
                        for itemName in itemNameList:
                                data = delete_quote(self.get(itemName, layer))                                
                                myList[layer][itemName] = data
                return myList

        def get_inputToSettingList(self):
                myList = itemList(settingLayerNameList, settingNameList)
                for layer in settingLayerNameList:
                        for itemName in settingNameList:
                                data = delete_quote(self.get_setting(itemName))
                                myList[layer][itemName] = data
                return myList

        def set_itemListToInput(self, itemList):
                self.delete_all()
                for layer in itemLayerNameList:
                        for itemName in itemNameList:                                
                                self.set(itemName, layer, itemList[layer][itemName])

        def set_settingListToInput(self, itemList):
                for layer in settingLayerNameList:
                        for itemName in settingNameList:
                                self.set_setting(itemName, itemList["PATH"][itemName])

        def delete_all(self):
                for layer in itemLayerNameList:
                        for itemName in itemNameList:
                                self.delete(itemName, layer)


class outputController:
        def __init__(self, inputController, queueController, fileController, pathData):
                self.inputController = inputController
                self.queueController = queueController
                self.fileController = fileController
                self.pathData = pathData

        def get_taskData(self, orderData):
                myTaskData = taskData()
                for layer in itemLayerNameList:
                        for itemName in itemNameList:
                                value = orderData.get(itemName, "MAIN")
                                myTaskData.set(itemName, value)

                if orderData.get_variant():
                        for key in orderData.variant:
                                if not key == "":
                                        value = myTaskData.get(key)
                                        value = float(value)
                                        value += orderData.variant[key]
                                        if key == "strength" or key == "scale":
                                                value = round(value, 1)
                                        else:
                                                value = int(value)
                                        value = str(value)
                                        myTaskData.set(key, value)
                return myTaskData

        def do_output(self):
                for i in range(10):
                        if not myInputController.check_setting():
                                myInputController.prepare_settingDlg()
                        else:
                                break
                self.pathData.get_pathFromSetting()
                myOrderData = orderData()
                myItemList = self.inputController.get_inputToItemList()
                myOrderData.set_itemList(myItemList)                                
                self.fileController.set_log(myItemList)

                myOrderLogController = orderLogController(myOrderData, self.pathData)
                myOrderLogController.make_logFile()

                optionInfo = myOrderData.get_optionInfo()
                if len(optionInfo.keys()) == 0:
                        self.with_noLoop(myOrderData)
                else:
                        self.with_loop(myOrderData, optionInfo)

        def with_noLoop(self, orderData):

                myTaskData = self.get_taskData(orderData)
                self.queueController.push_qWaiting(myTaskData)

        def with_loop(self, orderData, optionInfo):
                # ループの最大数は5項目のため、forの入れ子は5つ
                # ループ可能項目を増やしたら、入れ子も追加する
                loopName = ["", "", "", "", ""]
                loopWidth = [0, 0, 0, 0, 0]
                loopMax = [1, 1, 1, 1, 1]
                i = 0
                for itemName in optionInfo:

                        loopName[i] = itemName
                        loopWidth[i] = optionInfo[itemName]["OP1"]
                        loopMax[i] = optionInfo[itemName]["OP2"]
                        i += 1
                variant = {}

                for i in range(loopMax[0]):
                        for j in range(loopMax[1]):
                                for k in range(loopMax[2]):
                                        for l in range(loopMax[3]):
                                                for m in range(loopMax[4]):
                                                        variant={loopName[0] : loopWidth[0] * i,
                                                                loopName[1] : loopWidth[1] * j,
                                                                loopName[2] : loopWidth[2] * k,
                                                                loopName[3] : loopWidth[3] * l,
                                                                loopName[4] : loopWidth[4] * m}
                                                        orderData.set_variant(variant)

                                                        myTaskData = self.get_taskData(orderData)
                                                        self.queueController.push_qWaiting(myTaskData)


class queueController:
        def __init__(self, inputController, threadPE, pathData):
                self.qWaiting = queue.Queue()
                self.qProcessing = queue.Queue()
                self.qDone = queue.Queue()

                self.inputController = inputController
                self.threadPE = threadPE
                self.pathData = pathData

        def draw_qBox(self):
                self.inputController.delete_qBox()
                for Data in self.qProcessing.queue:
                        cmd = Data.get_cmd()
                        cmd = delete_space(cmd)
                        cmd = delete_quote(cmd)
                        cmd = "<Processing>" + cmd + "\n"
                        self.inputController.set_qBox("1.0", cmd)
                for Data in self.qWaiting.queue:
                        cmd = Data.get_cmd()
                        cmd = delete_space(cmd)
                        cmd = delete_quote(cmd)
                        cmd = "<Waiting>" + cmd + "\n"
                        self.inputController.set_qBox("end", cmd)

        def push_qWaiting(self, taskData):
                self.qWaiting.put(taskData)
                if self.qProcessing.empty():
                        self.push_qProcessing()
                self.draw_qBox()

        def push_qProcessing(self):
                nowData = self.qWaiting.get()
                self.qProcessing.put(nowData)

                future = self.threadPE.submit(do_bat, nowData, self.pathData)

                future.add_done_callback(self.push_qDone)
                self.draw_qBox()

        def push_qDone(self, future):
                doneData = self.qProcessing.get()
                self.qDone.put(doneData)

                if not self.qWaiting.empty():
                        self.push_qProcessing()
                self.draw_qBox()

        def kill_qWaiting(self):
                if not self.qWaiting.empty():
                        self.qWaiting.get()
                self.draw_qBox() 

        def allkill_qWaiting(self):
                for task in range(self.qWaiting.qsize()):
                        self.qWaiting.get()
                self.draw_qBox() 


class orderLogController:
        def __init__(self, orderData, pathData):
                 self.orderData = orderData
                 self.pathData = pathData

        def make_logFile(self):
                nowTime = datetime.datetime.now(JST)
                folderPath = self.get_folderName()
                logText = self.get_logText()
                nowTimeText = nowTime.strftime('%Y_%m_%d_%H%M%S')
                os.makedirs(folderPath, exist_ok = True)
                f = open(folderPath + "/" + nowTimeText + ".txt", "w")
                f.write(logText)
                f.close()
                
        def get_logText(self):
                text = []
                text.append(self.orderData.get("prompt", "MAIN") + "\n\n")

                newList = {}
                for itemName in itemNameList:
                        newList[itemName] = {}

                itemList = self.orderData.get_itemList()
                for layer in itemList:
                        for itemName in itemList[layer]:
                                newList[itemName].update({layer : itemList[layer][itemName]})

                for itemName in itemNameList:
                        if not itemName == "prompt" and not itemName == "plms":
                                text.append(itemName + ":")
                                text.append(newList[itemName]["MAIN"] + " ")
                                if not newList[itemName]["OP2"] == "" and not newList[itemName]["OP2"] == "1":
                                        text.append(" (" + newList[itemName]["OP1"] + "刻みで")
                                        text.append(newList[itemName]["OP2"] + "種出力)")
                                text.append("\n")
                logText = ""

                for i in range(len(text)):
                       logText = logText + text[i]
                return logText

        def get_folderName(self):
                prompt = self.orderData.get("prompt", "MAIN")
                outPass = self.get_outPass()

                folderName = ""
                folderName = os.path.join(outPass, "_".join(re.split(":| ", prompt)))[:150]
                return folderName

        def get_outPass(self):
                sdRootPath = self.pathData.get("sdRoot", "PATH")
                outdir = self.orderData.get("outdir", "MAIN")
                if self.orderData.get("init_img", "MAIN") == "":
                        mode = "txt"
                else:
                        mode = "img"
                
                if outdir == "" and mode == "txt":
                        outPath = sdRootPath + "/outputs/txt2img-samples"
                elif outdir == "" and mode == "img":
                        outPath = sdRootPath + "/outputs/img2img-samples"
                else:
                        outPath = outdir
                return outPath
                        
        
def do_bat(taskData, pathData):
        cmd = taskData.get_cmd()
        sdRootPath = pathData.get("sdRoot", "PATH")

        sdRootPathDrive = pathData.get_sdRootDrive()
        condaPath = pathData.get("condaActivateBat", "PATH")
        sdOptPath = taskData.get_execute(pathData)

        print("call " + batPath + " " + cmd + " " + sdRootPath + 
                        " " + sdRootPathDrive + " " + condaPath + " " + sdOptPath)

        subprocess.run(
                        "call " + batPath + " " + cmd + " " + sdRootPath + 
                        " " + sdRootPathDrive + " " + condaPath + " " + sdOptPath,
                        shell=True,
                        encoding="shift-jis")


def do_setting(self, dlg, fileController):
        myList = itemList(settingLayerNameList, settingNameList)
        myList["PATH"]["sdRoot"] = dlg.var_sdRoot
        myList["PATH"]["condaActivateBat"] = dlg.var_condaActivateBat
        myList["PATH"]["sdOptimizedTxt2img"] = dlg.var_sdOptimizedTxt2img
        myList["PATH"]["sdOptimizedImg2img"] = sdOptimizedImg2img

        fileController.set_setting(myList)

        dlg.destroy()


# ここから起動後処理
myThreadPE = threadPE(max_workers=1)

myFileController = fileController()
myPathData = pathData(myFileController)

myMainGUI = mainGUI()
myMainGUI.grid()
myInputController = inputController(myMainGUI, myFileController)

myQueueController = queueController(myInputController, myThreadPE, myPathData)
myOutputController = outputController(myInputController, myQueueController, myFileController, myPathData)

# 前回データをInputにセット
logItemList = myFileController.get_log()
# promptが空なら前回データなしと見なし、セットしない（初期値を残す）
if not logItemList["MAIN"]["prompt"] == "":
        myInputController.set_itemListToInput(logItemList)
a = 0
myMainGUI.draw_number(a, a, a)

# 設定データをInputにセット
# 設定データがない場合や、あっても空欄がある場合、設定ダイアログを開く
if myFileController.check_setting():
        settingItemList = myFileController.get_setting()
        if not myInputController.check_setting():
                myInputController.prepare_settingDlg()
else:
        myInputController.prepare_settingDlg()

# os.system('PAUSE')
# ウインドウ状態の維持
myMainGUI.mainloop()
