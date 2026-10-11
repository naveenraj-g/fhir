"""Group the flat PlanDefinition child rows by their owner so the mappers can rebuild the nested structure."""

from __future__ import annotations

from collections import defaultdict
from types import SimpleNamespace


def build_index(pd) -> SimpleNamespace:
    """
    Everything is loaded flat (`plan_definition_id` on each row); this re-groups rows by action / trigger / goal.
    Sibling order follows `position` (actions) or insertion order (the rest).
    """
    idx = SimpleNamespace(
        actions_by_parent=defaultdict(list),
        codes=defaultdict(list),          # action_id -> [action_code rows] (kind code|reason)
        goal_ids=defaultdict(list),
        triggers=defaultdict(list),
        conditions=defaultdict(list),
        drs_by_action=defaultdict(list),  # action_id -> input / output rows
        drs_by_trigger=defaultdict(list),
        related=defaultdict(list),
        participants=defaultdict(list),
        dynamic=defaultdict(list),
        docs_by_action=defaultdict(list),
        docs_by_goal=defaultdict(list),
        plan_artifacts=[],
    )
    for a in sorted(pd.actions or [], key=lambda x: (x.position or 0, x.id)):
        idx.actions_by_parent[a.parent_action_id].append(a)
    for r in sorted(pd.action_codes or [], key=lambda x: x.id):
        idx.codes[r.action_id].append(r)
    for r in sorted(pd.action_goal_ids or [], key=lambda x: x.id):
        idx.goal_ids[r.action_id].append(r)
    for r in sorted(pd.triggers or [], key=lambda x: x.id):
        idx.triggers[r.action_id].append(r)
    for r in sorted(pd.conditions or [], key=lambda x: x.id):
        idx.conditions[r.action_id].append(r)
    for r in sorted(pd.data_requirements or [], key=lambda x: x.id):
        if r.trigger_id is not None:
            idx.drs_by_trigger[r.trigger_id].append(r)
        elif r.action_id is not None:
            idx.drs_by_action[r.action_id].append(r)
    for r in sorted(pd.related_actions or [], key=lambda x: x.id):
        idx.related[r.action_id].append(r)
    for r in sorted(pd.participants or [], key=lambda x: x.id):
        idx.participants[r.action_id].append(r)
    for r in sorted(pd.dynamic_values or [], key=lambda x: x.id):
        idx.dynamic[r.action_id].append(r)
    for r in sorted(pd.related_artifacts or [], key=lambda x: x.id):
        scope = getattr(r.scope, "value", r.scope)
        if scope == "action":
            idx.docs_by_action[r.action_id].append(r)
        elif scope == "goal":
            idx.docs_by_goal[r.goal_id].append(r)
        else:
            idx.plan_artifacts.append(r)
    return idx
