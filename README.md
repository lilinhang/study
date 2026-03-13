# 机电设备维保项目管理系统（Django API 原型）

该仓库提供一个可落地的后端原型，覆盖你提出的核心闭环流程：

- 项目受理建档、分级审批、自动派工
- 执行记录与备件消耗
- 自动费用核算与结算
- RBAC 可扩展（基于 Django 权限体系）

## 快速启动

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## 主要 API

- `POST /api/projects/` 创建项目（自动生成项目编号）
- `POST /api/projects/{id}/submit_for_approval/` 按金额生成审批任务
- `POST /api/projects/{id}/auto_dispatch/` 智能派工
- `POST /api/projects/{id}/create_settlement/` 自动核算费用
- `POST /api/approvals/{id}/decide/` 审批通过/驳回

## 说明

- 当前为 MVP 版本，便于你继续扩展前端（Vue）与外部系统对接（ERP/CRM/MES）。
- 通知接口、地图派工 UI、报表可在此基础上分阶段添加。
