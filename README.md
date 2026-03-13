# 机电设备维保项目管理系统

你可以直接运行网页版本（无需安装第三方依赖），也可继续扩展 Django 后端原型。

## 1) 直接访问网页（推荐，开箱即用）

```bash
python serve.py
```

打开浏览器访问：`http://127.0.0.1:8000`

### 网页版已支持

- 项目创建（必填项校验）
- 按金额显示审批层级提示
- 项目流程一键推进（审核中 → 已派工 → 执行中 → 待验收 → 待结算 → 已归档）
- 项目总览统计（总数/进行中/已归档/紧急）
- 本地数据持久化（浏览器 localStorage）

## 2) Django API 原型（可继续二次开发）

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

> 若当前环境受网络代理限制，`pip install` 可能失败；此时仍可先使用第 1 部分网页版本进行业务演示。
