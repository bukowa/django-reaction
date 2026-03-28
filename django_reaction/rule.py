import json
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.functional import Promise


class AlpineRuleEncoder(DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, Promise):
            return str(o)
        return super().default(o)


def _safe_json(value):
    return json.dumps(value, cls=AlpineRuleEncoder)


class Condition:
    def __and__(self, other):
        return AndCondition(self, other)

    def __or__(self, other):
        return OrCondition(self, other)

    def to_js(self) -> str:
        raise NotImplementedError

    def get_dependencies(self) -> set:
        raise NotImplementedError

    def __eq__(self, other):
        other_node = other if isinstance(other, Condition) else Value(other)
        return Equals(self, other_node)

    def __ne__(self, other):
        other_node = other if isinstance(other, Condition) else Value(other)
        return NotEquals(self, other_node)

    def __gt__(self, other):
        other_node = other if isinstance(other, Condition) else Value(other)
        return GreaterThan(self, other_node)

    def contains(self, other):
        other_node = other if isinstance(other, Condition) else Value(other)
        return Contains(self, other_node)


class Value(Condition):
    def __init__(self, val):
        self.val = val

    def to_js(self):
        return _safe_json(self.val)

    def get_dependencies(self):
        return set()


class FieldValue(Condition):
    def __init__(self, name):
        self.name = name

    def to_js(self):
        return self.name

    def get_dependencies(self):
        return {self.name}


class Field:
    def __init__(self, name):
        self.name = name

    @property
    def value(self):
        return FieldValue(self.name)


class AndCondition(Condition):
    def __init__(self, left, right):
        self.left = left if isinstance(left, Condition) else Value(left)
        self.right = right if isinstance(right, Condition) else Value(right)

    def to_js(self):
        return f"({self.left.to_js()} && {self.right.to_js()})"

    def get_dependencies(self):
        return self.left.get_dependencies() | self.right.get_dependencies()


class OrCondition(Condition):
    def __init__(self, left, right):
        self.left = left if isinstance(left, Condition) else Value(left)
        self.right = right if isinstance(right, Condition) else Value(right)

    def to_js(self):
        return f"({self.left.to_js()} || {self.right.to_js()})"

    def get_dependencies(self):
        return self.left.get_dependencies() | self.right.get_dependencies()


class Equals(Condition):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def to_js(self):
        return f"({self.left.to_js()} == {self.right.to_js()})"

    def get_dependencies(self):
        return self.left.get_dependencies() | self.right.get_dependencies()


class NotEquals(Condition):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def to_js(self):
        return f"({self.left.to_js()} != {self.right.to_js()})"

    def get_dependencies(self):
        return self.left.get_dependencies() | self.right.get_dependencies()


class GreaterThan(Condition):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def to_js(self):
        return f"(Number({self.left.to_js()}) > Number({self.right.to_js()}))"

    def get_dependencies(self):
        return self.left.get_dependencies() | self.right.get_dependencies()


class Contains(Condition):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def to_js(self):
        val_js = self.left.to_js()
        target_js = self.right.to_js()
        return f"(Array.isArray({val_js}) ? {val_js}.includes({target_js}) : String({val_js}).includes({target_js}))"

    def get_dependencies(self):
        return self.left.get_dependencies() | self.right.get_dependencies()


class Rule:
    def __init__(self):
        self._target_attrs = {}
        self._condition = None
        self._all_dependencies = set()

    def when(self, condition):
        if not isinstance(condition, Condition):
            raise ValueError("when() requires a Condition instance (e.g., Field('engine') == 'value').")
        self._condition = condition
        return self

    def _add_to_target(self, target, js_code, bind_model=False):
        if target not in self._target_attrs:
            self._target_attrs[target] = {"x-init": []}
            if bind_model:
                self._target_attrs[target]["x-model"] = target
        self._target_attrs[target]["x-init"].append(js_code)

    def get_attrs_for_field(self, field_name):
        attrs = {}
        if field_name in self._all_dependencies:
            attrs["x-model"] = field_name

        if field_name in self._target_attrs:
            orig = self._target_attrs[field_name].copy()
            if "x-init" in orig:
                attrs['x-init'] = " ".join(orig['x-init'])
            if "x-model" in orig:
                attrs['x-model'] = orig['x-model']

        return attrs

    def show(self, target):
        if isinstance(target, str): target = Field(target)
        target_name = target.name
        
        deps = self._condition.get_dependencies() if self._condition else set()
        self._all_dependencies.update(deps)
        js_cond = self._condition.to_js() if self._condition else "true"

        watches = " ".join([f"$watch('{dep}', evaluate);" for dep in deps])
        js = f"""
            (() => {{
                const evaluate = () => {{
                    const el = $el.closest('.form-row');
                    if(el) el.style.display = ({js_cond}) ? '' : 'none';
                }};
                {watches}
                evaluate();
            }})();
        """
        self._add_to_target(target_name, js)
        return self

    def hide(self, target):
        if isinstance(target, str): target = Field(target)
        target_name = target.name
        
        deps = self._condition.get_dependencies() if self._condition else set()
        self._all_dependencies.update(deps)
        js_cond = self._condition.to_js() if self._condition else "true"

        watches = " ".join([f"$watch('{dep}', evaluate);" for dep in deps])
        js = f"""
            (() => {{
                const evaluate = () => {{
                    const el = $el.closest('.form-row');
                    if(el) el.style.display = ({js_cond}) ? 'none' : '';
                }};
                {watches}
                evaluate();
            }})();
        """
        self._add_to_target(target_name, js)
        return self

    def map_to(self, target, source, data_map):
        if isinstance(target, str): target = Field(target)
        if isinstance(source, str): source = Field(source)

        target_name = target.name
        source_name = source.name
        self._all_dependencies.add(source_name)

        deps = self._condition.get_dependencies() if self._condition else set()
        deps.add(source_name)
        self._all_dependencies.update(deps)

        js_cond = self._condition.to_js() if self._condition else "true"
        js_map = _safe_json(data_map)

        watches = " ".join([f"$watch('{dep}', evaluate);" for dep in deps])
        js = f"""
            (() => {{
                const map_data = {js_map};
                const evaluate = () => {{
                    if ({js_cond} && map_data[{source_name}] !== undefined) {{
                        {target_name} = map_data[{source_name}];
                    }}
                }};
                {watches}
                evaluate();
            }})();
        """
        self._add_to_target(target_name, js, bind_model=True)
        return self

    def fetch(self, endpoint_url, target, source):
        if isinstance(target, str): target = Field(target)
        if isinstance(source, str): source = Field(source)

        target_name = target.name
        source_name = source.name
        self._all_dependencies.add(source_name)

        deps = self._condition.get_dependencies() if self._condition else set()
        deps.add(source_name)
        self._all_dependencies.update(deps)

        js_cond = self._condition.to_js() if self._condition else "true"
        safe_url = _safe_json(endpoint_url)

        watches = " ".join([f"$watch('{dep}', evaluate);" for dep in deps])
        js = f"""
            (() => {{
                const evaluate = async () => {{
                    if ({js_cond}) {{
                        const val = {source_name};
                        if (!val) return;
                        const url = {safe_url} + '?q=' + encodeURIComponent(val);
                        try {{
                            const resp = await fetch(url);
                            const data = await resp.json();
                            {target_name} = JSON.stringify(data);
                        }} catch (e) {{
                            console.error("error fetch:", e);
                        }}
                    }}
                }};
                {watches}
            }})();
        """
        self._add_to_target(target_name, js, bind_model=True)
        return self
