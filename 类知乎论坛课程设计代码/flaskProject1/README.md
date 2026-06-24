# 知乎风格问答平台

一个基于 Flask 的问答平台项目，实现了用户注册、登录、提问、回答、评论、点赞等功能。

## 技术栈

- **框架**: Flask 2.0+
- **数据库**: MySQL
- **ORM**: SQLAlchemy
- **认证**: Flask-Login
- **安全**: Flask-Talisman, Flask-Limiter
- **前端**: HTML, CSS, JavaScript

## 功能特性

- 用户注册、登录、注销
- 问题发布、编辑、删除
- 回答发布、删除、点赞
- 评论功能
- 话题管理
- 用户个人主页
- 热门问题推荐

## 环境要求

- Python 3.8+
- MySQL 5.7+

## 安装步骤

### 1. 克隆项目

```bash
git clone <repository-url>
cd flaskProject1
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置数据库

1. 创建 MySQL 数据库：
```sql
CREATE DATABASE zhihu;
```

2. 执行数据库初始化脚本：
```bash
mysql -u root -p zhihu < DBLabScript_22251236.sql
mysql -u root -p zhihu < stored_procedures.sql
mysql -u root -p zhihu < triggers.sql
```

3. 修改 `app.py` 中的数据库配置：
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost/zhihu'
app.config['SECRET_KEY'] = 'your-secret-key-here'
```

### 5. 运行项目

```bash
python app.py
```

访问 http://localhost:5000 查看应用。

## 项目结构

```
flaskProject1/
├── app.py                 # 主应用文件
├── requirements.txt       # 依赖列表
├── DBLabScript_22251236.sql  # 数据库初始化脚本
├── stored_procedures.sql  # 存储过程
├── triggers.sql           # 触发器
├── .gitignore             # Git 忽略配置
├── README.md              # 项目说明
└── templates/             # HTML 模板
    ├── index.html         # 首页
    ├── login.html         # 登录页
    ├── register.html      # 注册页
    └── ...
```

## API 接口

### 话题详情
```
GET /api/topic/<topic_id>
```

## 安全注意事项

1. 生产环境请将 `Talisman` 的 `force_https` 设置为 `True`
2. 使用环境变量存储敏感信息（数据库密码、SECRET_KEY）
3. 定期更新依赖包

## License

MIT License