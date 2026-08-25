"""Minimal semantic schematic model: Component, Pin, Net, Schematic.

Electrical connectivity only — no coordinates, no rendering. See
requirements section 5/6/7 for the split between electrical model and
visual layout.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


class SchematicError(Exception):
    """Base error for structural problems in the semantic model."""


class ComponentNotFoundError(SchematicError):
    pass


class PinNotFoundError(SchematicError):
    pass


class DuplicateComponentError(SchematicError):
    pass


@dataclass
class Pin:
    number: str
    name: str
    electrical_type: str = "passive"
    side: str | None = None
    orientation: str | None = None
    hidden: bool = False

    def to_dict(self) -> dict:
        return {
            "number": self.number,
            "name": self.name,
            "electrical_type": self.electrical_type,
            "side": self.side,
            "orientation": self.orientation,
            "hidden": self.hidden,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Pin:
        return cls(
            number=data["number"],
            name=data["name"],
            electrical_type=data.get("electrical_type", "passive"),
            side=data.get("side"),
            orientation=data.get("orientation"),
            hidden=data.get("hidden", False),
        )


@dataclass
class Component:
    id: str
    library_id: str
    reference: str | None = None
    value: str | None = None
    label: str | None = None
    pins: list[Pin] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    placement_hint: dict | None = None

    def get_pin(self, ref: str) -> Pin:
        """Look up a pin by number first, then by name."""
        for pin in self.pins:
            if pin.number == ref:
                return pin
        for pin in self.pins:
            if pin.name == ref:
                return pin
        raise PinNotFoundError(f"{self.id} has no pin '{ref}'")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "library_id": self.library_id,
            "reference": self.reference,
            "value": self.value,
            "label": self.label,
            "pins": [p.to_dict() for p in self.pins],
            "metadata": self.metadata,
            "placement_hint": self.placement_hint,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Component:
        return cls(
            id=data["id"],
            library_id=data["library_id"],
            reference=data.get("reference"),
            value=data.get("value"),
            label=data.get("label"),
            pins=[Pin.from_dict(p) for p in data.get("pins", [])],
            metadata=data.get("metadata", {}),
            placement_hint=data.get("placement_hint"),
        )


@dataclass
class Net:
    name: str
    nodes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"name": self.name, "nodes": list(self.nodes)}

    @classmethod
    def from_dict(cls, data: dict) -> Net:
        return cls(name=data["name"], nodes=list(data.get("nodes", [])))


def _split_node(node: str) -> tuple[str, str]:
    if "." not in node:
        raise SchematicError(f"invalid pin reference '{node}', expected 'COMPONENT.PIN'")
    component_id, pin_ref = node.split(".", 1)
    return component_id, pin_ref


@dataclass
class Schematic:
    name: str
    components: dict[str, Component] = field(default_factory=dict)
    nets: dict[str, Net] = field(default_factory=dict)
    _net_counter: int = field(default=0, repr=False)

    # -- components ---------------------------------------------------

    def add_component(self, component: Component) -> Component:
        if component.id in self.components:
            raise DuplicateComponentError(f"component id '{component.id}' already exists")
        self.components[component.id] = component
        return component

    def remove_component(self, component_id: str) -> None:
        if component_id not in self.components:
            raise ComponentNotFoundError(f"unknown component '{component_id}'")
        del self.components[component_id]
        prefix = f"{component_id}."
        empty_nets = []
        for net_name, net in self.nets.items():
            net.nodes = [n for n in net.nodes if not n.startswith(prefix)]
            if not net.nodes:
                empty_nets.append(net_name)
        for net_name in empty_nets:
            del self.nets[net_name]

    # -- pin resolution -------------------------------------------------

    def _canonical_node(self, node: str) -> str:
        component_id, pin_ref = _split_node(node)
        component = self.components.get(component_id)
        if component is None:
            raise ComponentNotFoundError(f"unknown component '{component_id}'")
        pin = component.get_pin(pin_ref)
        return f"{component_id}.{pin.number}"

    def _find_net_of(self, node: str) -> Net | None:
        for net in self.nets.values():
            if node in net.nodes:
                return net
        return None

    def _new_net_name(self) -> str:
        self._net_counter += 1
        return f"N${self._net_counter}"

    # -- connections ----------------------------------------------------

    def connect(self, pin_a: str, pin_b: str) -> str:
        """Connect two pins, creating or merging nets as needed. Returns the net name."""
        node_a = self._canonical_node(pin_a)
        node_b = self._canonical_node(pin_b)
        net_a = self._find_net_of(node_a)
        net_b = self._find_net_of(node_b)

        if net_a is None and net_b is None:
            name = self._new_net_name()
            self.nets[name] = Net(name=name, nodes=[node_a, node_b])
            return name

        if net_a is not None and net_b is None:
            if node_b not in net_a.nodes:
                net_a.nodes.append(node_b)
            return net_a.name

        if net_a is None and net_b is not None:
            if node_a not in net_b.nodes:
                net_b.nodes.append(node_a)
            return net_b.name

        if net_a is net_b:
            return net_a.name

        # merge net_b into net_a
        for node in net_b.nodes:
            if node not in net_a.nodes:
                net_a.nodes.append(node)
        del self.nets[net_b.name]
        return net_a.name

    def connect_net(self, net_name: str, pins: list[str]) -> str:
        """Connect all given pins into a single named net, merging existing nets if needed."""
        net = self.nets.get(net_name)
        if net is None:
            net = Net(name=net_name)
            self.nets[net_name] = net

        for pin_ref in pins:
            node = self._canonical_node(pin_ref)
            existing = self._find_net_of(node)
            if existing is net:
                continue
            if existing is None:
                net.nodes.append(node)
                continue
            # merge the pin's existing net into `net`
            for other_node in existing.nodes:
                if other_node not in net.nodes:
                    net.nodes.append(other_node)
            del self.nets[existing.name]

        return net.name

    def disconnect(self, pin: str) -> None:
        node = self._canonical_node(pin)
        net = self._find_net_of(node)
        if net is None:
            return
        net.nodes.remove(node)
        if not net.nodes:
            del self.nets[net.name]

    def rename_net(self, old_name: str, new_name: str) -> None:
        if old_name not in self.nets:
            raise SchematicError(f"unknown net '{old_name}'")
        if new_name in self.nets and new_name != old_name:
            raise SchematicError(f"net '{new_name}' already exists")
        net = self.nets.pop(old_name)
        net.name = new_name
        self.nets[new_name] = net

    def node_to_net_map(self) -> dict[str, str]:
        return {node: net.name for net in self.nets.values() for node in net.nodes}

    # -- serialization ----------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "components": [c.to_dict() for c in self.components.values()],
            "nets": [n.to_dict() for n in self.nets.values()],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Schematic:
        schematic = cls(name=data.get("name", "schematic"))
        for component_data in data.get("components", []):
            schematic.add_component(Component.from_dict(component_data))
        for net_data in data.get("nets", []):
            net = Net.from_dict(net_data)
            schematic.nets[net.name] = net
        return schematic

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False))

    @classmethod
    def load(cls, path: str | Path) -> Schematic:
        return cls.from_dict(json.loads(Path(path).read_text()))
