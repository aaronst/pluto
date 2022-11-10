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


from json import dumps

from synapse.telepath import Proxy
from textual.app import ComposeResult
from textual.css.query import NoMatches
from textual.message import Message, MessageTarget
from textual.widgets import DataTable, Input, Static


class Summary(Static):
    """A widget to display Storm query summaries."""

    DEFAULT_CSS = """
    Summary {
        content-align: center middle;
        height: 3;
        width: 30;
    }

    Summary .success {
        border: round $success;
        color: $success;
    }

    Summary .error {
        border: round $error;
        color: $error;
    }
    """

    def success(self, fini: dict) -> None:
        """Set content based on a given fini message."""

        self.add_class("success")
        self.update(f"{fini['count']} in {fini['took'] / 1000.0:.2f}s")


class QueryBar(Static):
    """A widget for Storm query input and results summary."""

    DEFAULT_CSS = """
    QueryBar {
        dock: top;
        layout: horizontal;
    }

    QueryBar > #query {
        width: 1fr;
    }
    """

    class Submitted(Message):
        """Storm query submitted."""

        def __init__(self, sender: MessageTarget, query: str) -> None:
            self.query = query
            super().__init__(sender)

    def compose(self) -> ComposeResult:
        """Create child widgets."""

        yield Input(placeholder="storm>", id="query")
        yield Summary(id="summary")

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        """User input submitted."""

        summary = self.query_one(Summary)
        summary.remove_class("error", "success")
        summary.update("running...")

        await self.emit(self.Submitted(self, message.value))

    def on_mount(self) -> None:
        """Focus on Input."""

        self.query_one(Input).focus()


class Storm(Static):
    """A widget to submit Storm queries and view results."""

    def __init__(self, core: Proxy, *args, **kwargs) -> None:
        """Initialize this instance."""

        self.core = core
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        """Create child widgets."""

        yield QueryBar(id="query-bar")

    async def on_query_bar_submitted(self, message: QueryBar.Submitted) -> None:
        """Handle a submitted Storm query."""

        try:
            self.query_one("#nodes").remove()
        except NoMatches:
            pass

        nodes = DataTable(id="nodes")
        nodes.add_columns("node")

        i = 0
        rows = []

        async for message_type, message_data in self.core.storm(message.query):
            if message_type == "node":
                i += 1
                rows.append((dumps(message_data, indent=None),))

                if i % 100 == 0:
                    nodes.add_rows(rows)
                    rows.clear()

            elif message_type == "fini":
                summary = self.query_one(Summary)
                summary.success(message_data)

        if rows:
            nodes.add_rows(rows)

        await self.mount(nodes)
