## 使用说明
### 1. 创建docker镜像
```
docker build -t clhkxy_app .
```
### 2. 运行docker镜像
```
docker run -it -p 5000:5000 -v /主机路径:/app/data clhkxy_app 
```