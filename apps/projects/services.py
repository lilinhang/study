from dataclasses import dataclass
from decimal import Decimal
from math import acos, cos, radians, sin
from typing import Iterable

from .models import ApprovalRecord, Engineer, PartUsage, Project


@dataclass
class DispatchCandidate:
    engineer: Engineer
    score: float


def approval_nodes_by_amount(amount: Decimal) -> list[str]:
    if amount <= Decimal("10000"):
        return [ApprovalRecord.Node.SUPERVISOR]
    if amount <= Decimal("50000"):
        return [ApprovalRecord.Node.SUPERVISOR, ApprovalRecord.Node.TECH_LEAD]
    return [
        ApprovalRecord.Node.SUPERVISOR,
        ApprovalRecord.Node.TECH_LEAD,
        ApprovalRecord.Node.FINANCE,
        ApprovalRecord.Node.GM,
    ]


def _distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius = 6371
    return radius * acos(
        sin(radians(lat1)) * sin(radians(lat2))
        + cos(radians(lat1)) * cos(radians(lat2)) * cos(radians(lng1 - lng2))
    )


def choose_engineer(project: Project, engineers: Iterable[Engineer], site_lat: float, site_lng: float) -> DispatchCandidate | None:
    candidates: list[DispatchCandidate] = []
    for eng in engineers:
        if not eng.is_available:
            continue
        distance_score = 0.0
        if eng.latitude is not None and eng.longitude is not None:
            distance = _distance_km(site_lat, site_lng, eng.latitude, eng.longitude)
            distance_score = max(0.0, 100.0 - distance)

        skill_score = 50.0 if project.project_type in eng.skills else 0.0
        level_score = {
            Engineer.SkillLevel.JUNIOR: 10,
            Engineer.SkillLevel.MIDDLE: 20,
            Engineer.SkillLevel.SENIOR: 30,
        }[eng.skill_level]

        total = distance_score * 0.4 + skill_score * 0.4 + level_score * 0.2
        candidates.append(DispatchCandidate(engineer=eng, score=total))

    if not candidates:
        return None
    return sorted(candidates, key=lambda item: item.score, reverse=True)[0]


def calculate_settlement(project: Project, labor_hour_rate: Decimal, travel_cost: Decimal = Decimal("0"), other_cost: Decimal = Decimal("0")) -> dict[str, Decimal]:
    execution_records = project.execution_records.all()
    labor_hours = sum(record.work_hours for record in execution_records)

    labor_cost = labor_hours * labor_hour_rate
    part_cost = Decimal("0")

    part_usages = PartUsage.objects.filter(execution_record__project=project).select_related("spare_part")
    for usage in part_usages:
        part_cost += usage.spare_part.unit_cost * usage.quantity * Decimal("1.05")

    total = labor_cost + part_cost + travel_cost + other_cost
    return {
        "labor_cost": labor_cost.quantize(Decimal("0.01")),
        "part_cost": part_cost.quantize(Decimal("0.01")),
        "travel_cost": travel_cost.quantize(Decimal("0.01")),
        "other_cost": other_cost.quantize(Decimal("0.01")),
        "total_amount": total.quantize(Decimal("0.01")),
    }
