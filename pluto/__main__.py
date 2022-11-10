"""Main entry point.

Analysis tool and interface for Synapse.

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


from synapse.telepath import openurl, withTeleEnv
from textual.app import App, ComposeResult

from .widgets.login import Login
from .widgets.storm import Storm


class Pluto(App):
    """A Textual app for Pluto."""

    CSS_PATH = "css/pluto.css"
    TITLE = "pluto"

    def __init__(self, *args, **kwargs) -> None:
        """Initialize an instance."""

        self.core = None
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""

        yield Login()

    async def on_login_submitted(self, message: Login.Submitted) -> None:
        """Event handler for the login submission."""

        async with withTeleEnv():
            self.core = await openurl(message.value)

        await self.mount(Storm(self.core))


def main() -> None:
    """Main function."""

    app = Pluto()
    app.run()


if __name__ == "main":
    main()
