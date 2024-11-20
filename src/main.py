from wiz.wiz_convertor import WizConvertor

wiz_dir = input("笔记文件夹参考：Wiz安装路径/My Knowledge/Data/账号名\n输入为知笔记文件夹路径：")

wiz_convertor = WizConvertor(wiz_dir)

wiz_convertor.convert()
