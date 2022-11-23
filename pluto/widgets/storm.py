"""Storm widget.

A textual widget to submit Storm queries and view results.

Copyright 2022 Aaron Stephens

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


from collections import deque
from datetime import datetime
from json import dumps
from typing import Any

from synapse.cortex import CoreApi
from textual.app import ComposeResult
from textual.containers import Content, Vertical
from textual.events import Key
from textual.message import Message, MessageTarget
from textual.widgets import DataTable, Input, Static


class Summary(Static):
    """A widget to display Storm query summaries."""

    DEFAULT_CSS = """
    Summary {
        color: $text-disabled;
        content-align: center middle;
        height: auto;
        padding: 1 2 0 2;
        width: 100%;
    }

    Summary.running {
        border-bottom: hkey $accent;
    }

    Summary.error {
        border-bottom: hkey $error;
        color: $error;
    }

    Summary.success {
        border-bottom: hkey $success;
        color: $success;
    }
    """

    def error(self, err: tuple[str, dict]) -> None:
        """Set content based on a given err message."""

        self.remove_class("running")
        self.add_class("error")
        self.update(f"[b i]{err[0]}[/]: {err[1]['mesg']}")

    def success(self, fini: dict) -> None:
        """Set content based on a given fini message."""

        self.remove_class("running")
        self.add_class("success")
        self.update(f"[b]{fini['count']}[/] in [i]{fini['took'] / 1000.0:.2f}s")


class Query(Input):
    """A widget for inputting storm commands and queries."""

    class Submitted(Message):
        """Input submitted."""

        def __init__(self, sender: MessageTarget, query: str) -> None:
            self.query = query
            super().__init__(sender)

    def __init__(self, *args, max_history: int = 1000, **kwargs) -> None:
        self.history = deque(maxlen=max_history)
        self.history_index = 0
        super().__init__(*args, **kwargs)

    async def on_key(self, event: Key) -> None:
        """Key pressed."""

        if event.key == "down":
            if self.history_index > 0:
                self.history_index -= 1
        elif event.key == "up":
            if self.history_index < len(self.history) - 1:
                self.history_index += 1
        else:
            return

        self.value = self.history[self.history_index]
        self.cursor_position = len(self.value)


class QueryBar(Static):
    """A widget for Storm query input and results summary."""

    DEFAULT_CSS = """
    QueryBar {
        dock: top;
    }
    """

    class Submitted(Message):
        """Storm query submitted."""

        def __init__(self, sender: MessageTarget, query: str) -> None:
            self.query = query
            super().__init__(sender)

    def compose(self) -> ComposeResult:
        """Create child widgets."""

        yield Query(id="query", placeholder="storm>")
        yield Summary(id="summary", markup=True)

    async def on_query_submitted(self, message: Query.Submitted) -> None:
        """Storm query submitted."""

        query = self.get_child_by_id("query")
        assert isinstance(query, Query)
        query.history_index = 0

        if not query.history:
            query.history.append(message.query)
        elif message.query != query.history[0]:
            query.history.appendleft(message.query)

        summary = self.get_child_by_id("summary")
        assert isinstance(summary, Static)
        summary.remove_class("error", "success")
        summary.add_class("running")
        summary.update("[i]running...")

        await self.emit(self.Submitted(self, message.query))

    def on_mount(self) -> None:
        """Focus on Input."""

        self.get_child_by_id("query").focus()


# type alias for packed nodes
NodeType = tuple[tuple[str, int], dict[str, Any]]


class Nodes(Vertical):
    """A widget for displaying Synapse nodes."""

    DEFAULT_CSS = """
    Nodes {
        padding: 1 0 1 1;
    }
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.tables = {}

    def add_nodes(self, *nodes: NodeType) -> None:
        """Add nodes to their respective tables."""

        sorted_nodes = {}

        for node in nodes:
            # unpack the node
            (form, _), data = node
            row = (data["repr"],)

            try:
                sorted_nodes[form].append(row)
            except KeyError:
                sorted_nodes[form] = [row]

        for form, rows in sorted_nodes.items():
            # get the associated table or create one if it doesn't exist
            try:
                table = self.tables[form]
            except KeyError:
                table = DataTable()
                table.add_column(form)
                table.zebra_stripes = True
                self.tables[form] = table
                self.mount(table)

            # add rows to the table
            table.add_rows(rows)

    def clear(self) -> None:
        """Remove all tables."""

        for table in self.tables.values():
            table.remove()

        self.tables.clear()


class Console(Content):
    """A widget to display messages."""

    DEFAULT_CSS = """
    Console {
        background: $background;
        border-top: tall $accent;
        color: $text-disabled;
        dock: bottom;
        height: auto;
        max-height: 30%;
        overflow-y: auto;
        padding: 0 1 1 1;
    }
    """

    def __init__(self, *args, limit: int = 1000, **kwargs) -> None:
        self.first = 0
        self.limit = limit
        self.lines = 0
        super().__init__(*args, **kwargs)

    def print(self, text: str) -> None:
        """Add content and scroll to the bottom."""

        time = datetime.utcnow().isoformat(sep=" ", timespec="seconds")

        for line in [f"{time} - {line}" for line in text.splitlines()]:
            self.mount(Static(line, id=f"line-{self.lines}"))

            self.lines += 1

            if self.lines - self.first == self.limit:
                self.get_child_by_id(f"line-{self.first}").remove()
                self.first += 1

        self.scroll_end(animate=False)


class Storm(Static):
    """A widget to submit Storm queries and view results."""

    DEFAULT_CSS = """
    Storm {
        height: 100%;
        width: 100%;
    }
    """

    def __init__(self, core: CoreApi, *args, **kwargs) -> None:
        """Initialize this instance."""

        self.core = core
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        """Create child widgets."""

        yield QueryBar(id="query-bar")
        yield Nodes(id="nodes")
        yield Console(id="console")

    async def on_query_bar_submitted(self, message: QueryBar.Submitted) -> None:
        """Handle a submitted Storm query."""

        # whether previous data has been cleared
        cleared = False

        nodes = self.get_child_by_id("nodes")
        assert isinstance(nodes, Nodes)
        summary = self.get_widget_by_id("summary")
        assert isinstance(summary, Summary)
        console = self.get_child_by_id("console")
        assert isinstance(console, Console)

        # buffer 100 nodes at a time
        # TODO: is there an optimal number here?
        buffer = []
        limit = 100

        async for message_type, message_data in self.core.storm(
            message.query, opts={"repr": True}
        ):
            if message_type == "node":
                buffer.append(message_data)

                if len(buffer) == limit:
                    if not cleared:
                        # clear existing nodes
                        nodes.clear()
                        cleared = True

                    nodes.add_nodes(*buffer)
                    buffer.clear()

            elif message_type == "err":
                summary.error(message_data)
                break

            elif message_type == "fini":
                summary.success(message_data)

            elif message_type == "print":
                console.print(message_data["mesg"])

            else:
                console.print(dumps((message_type, message_data)))

        # add any remaining nodes
        if buffer:
            if not cleared:
                # clear existing nodes
                nodes.clear()

            nodes.add_nodes(*buffer)
