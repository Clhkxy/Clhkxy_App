## 使用说明
### 1. 创建docker镜像，创建文件目录及sqlite数据库。
```
mkdir data
sqlite3 Clhkxy_App.db ""
docker build -t clhkxy_app .
```
### 2. 运行docker镜像
```
docker run -it -p 5000:5000 -v ./data:/app/data -v ./Clhkxy_App.db:/app/Clhkxy_App.db clhkxy_app 
```