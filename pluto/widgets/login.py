"""Login widget.

A textual widget for logging into Synapse.

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


from rich.text import Text
from textual.app import ComposeResult
from textual.message import Message, MessageTarget
from textual.widgets import Input, Static


class Login(Static):
    """The login widget."""

    class Submitted(Message):
        """Login submitted message."""

        def __init__(self, sender: MessageTarget, value: str) -> None:
            self.value = value
            super().__init__(sender)

    def compose(self) -> ComposeResult:
        """Create child widgets for the login."""

        welcome = Text.from_markup(
            "Welcome to [bold cyan]Pluto[/], a [italic]terminal user-interface[/]"
            " for [green]Synapse[/]!\nPlease input your [green]Synapse[/] Telepath URL"
            " below and press [bold underline]Enter[/] to get started."
        )

        yield Static(welcome, id="welcome")
        yield Input(
            id="url",
            placeholder="aha://user@cortex.domain.com",
            value="aha://aaron@cortex.graph.money",
        )

    def on_mount(self) -> None:
        """Focus on Input."""

        self.query_one(Input).focus()

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        """Event handler for the url submission."""

        # stop message from bubbling to parent
        message.stop()

        # remove login widget from the dom
        self.remove()

        # emit our own special submitted message
        await self.emit(self.Submitted(self, message.value))
