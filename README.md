# buaa-nCov-autoDaka

使用 python - requests 库实现每日自动完成 BUAA 健康打卡。

默认是信息相较于前一天不发生改变，各种信息包括定位信息都与前一天一致，仅更新日期时间，然后提交。

完善的异常处理措施，每个步骤出错会再次执行，确保打卡成功率。

打卡成功或失败都会自动发 QQ 邮件提醒，手机 QQ 能直接看到邮箱提醒，非常方便。



## Usage

1. 打开 ```user.json```，输入统一认证账号和密码以及 QQ 邮箱。可以输入多个账号，逐一给多账号打卡；
2. 进入 web 网易邮箱，设置-账户，打开 smtp 服务，生成授权码；
3. 在 ```autoDaka.py``` 中的 ```mail_sender``` 和 ```mail_pass``` 中输入上述163 邮箱和授权码，该邮箱用于发送邮件；
4. 执行下列命令即可运行：

```bash
pip install requests
python autoDaka.py
```



## Scheduling Task

win10：此电脑 - 管理 - 任务计划程序，设置每日定时打卡任务；

Linux or Mac：使用 crontab 新增每日定时任务。