import flet as ft
import aiohttp
import asyncio
import random
import time
from typing import Optional
from fake_useragent import UserAgent
import ssl

# do not read that code pls


class StressTest:
    def __init__(self):
        self.running = False
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.start_time: Optional[float] = None
        self.ua = UserAgent()

    async def make_request(self, url: str, method: str, headers: dict, proxy: Optional[str] = None):
        try:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            async with aiohttp.ClientSession() as session:
                async with session.request(
                        method=method,
                        url=url,
                        headers=headers,
                        proxy=proxy,
                        ssl=ssl_context,
                        timeout=aiohttp.ClientTimeout(total=10),
                        data=random.randbytes(128)
                ) as response:
                    await response.text()
                    self.successful_requests += 1

        except Exception:
            self.failed_requests += 1
        finally:
            self.total_requests += 1


class StressTestGUI:
    def __init__(self):
        self.stress_test = StressTest()

    def main(self, page: ft.Page):
        page.title = "Web Stress Test Tool"
        page.theme_mode = ft.ThemeMode.DARK

        url_input = ft.TextField(label="Target URL", width=400)
        threads_input = ft.TextField(label="Concurrent Threads", value="100", width=200)
        duration_input = ft.TextField(label="Duration (seconds)", value="30", width=200)

        method_dropdown = ft.Dropdown(
            width=200,
            label="HTTP Method",
            options=[
                ft.dropdown.Option("GET"),
                ft.dropdown.Option("POST"),
                ft.dropdown.Option("HEAD")
            ],
            value="GET"
        )

        use_proxy = ft.Checkbox(label="Use Proxy", value=False)
        proxy_input = ft.TextField(label="Proxy URL (http://ip:port)", width=400, visible=False)

        status_text = ft.Text("Ready to start...")
        progress_bar = ft.ProgressBar(width=400, visible=False)

        stats_text = ft.Text()

        async def update_stats():
            while self.stress_test.running:
                if self.stress_test.start_time:
                    elapsed = time.time() - self.stress_test.start_time
                    rps = self.stress_test.total_requests / elapsed if elapsed > 0 else 0

                    stats_text.value = (
                        f"Total Requests: {self.stress_test.total_requests}\n"
                        f"Successful: {self.stress_test.successful_requests}\n"
                        f"Failed: {self.stress_test.failed_requests}\n"
                        f"Requests/sec: {rps:.2f}"
                    )
                    await page.update_async()
                await asyncio.sleep(1)

        async def start_test(e):
            if not url_input.value:
                status_text.value = "Please enter a valid URL"
                await page.update_async()
                return

            self.stress_test = StressTest()
            self.stress_test.running = True
            self.stress_test.start_time = time.time()

            threads = int(threads_input.value)
            duration = int(duration_input.value)

            status_text.value = "Test running..."
            progress_bar.visible = True
            await page.update_async()

            proxy = proxy_input.value if use_proxy.value else None

            async def worker():
                while self.stress_test.running:
                    headers = {
                        'User-Agent': self.stress_test.ua.random,
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Connection': 'keep-alive',
                    }

                    await self.stress_test.make_request(
                        url_input.value,
                        method_dropdown.value,
                        headers,
                        proxy
                    )

                    await asyncio.sleep(random.uniform(0.1, 0.3))

            tasks = [worker() for _ in range(threads)]
            stats_task = asyncio.create_task(update_stats())

            try:
                await asyncio.wait_for(asyncio.gather(*tasks), timeout=duration)
            except asyncio.TimeoutError:
                pass
            finally:
                self.stress_test.running = False
                await stats_task

                status_text.value = "Test completed"
                progress_bar.visible = False
                await page.update_async()

        def proxy_changed(e):
            proxy_input.visible = use_proxy.value
            page.update()

        use_proxy.on_change = proxy_changed

        start_button = ft.ElevatedButton(
            text="Start Test",
            on_click=start_test
        )

        page.add(
            ft.Column([
                ft.Text("Web Stress Test Tool", size=24, weight=ft.FontWeight.BOLD),
                url_input,
                ft.Row([threads_input, duration_input]),
                method_dropdown,
                use_proxy,
                proxy_input,
                start_button,
                status_text,
                progress_bar,
                stats_text
            ])
        )


if __name__ == "__main__":
    app = StressTestGUI()
    ft.app(target=app.main)