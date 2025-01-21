import flet as ft
import aiohttp
import asyncio
import random
import time
from typing import Optional
import ssl
import platform


class StressTest:
    def __init__(self):
        self.running = False
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.start_time: Optional[float] = None
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Android 14; Mobile; rv:121.0) Gecko/121.0 Firefox/121.0",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0"
        ]

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
                        timeout=aiohttp.ClientTimeout(total=10)
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
        self.is_mobile = platform.system() == "Android"

    def main(self, page: ft.Page):
        page.title = "Web Stress Test Tool"
        page.theme_mode = ft.ThemeMode.DARK
        page.window_width = 450 if not self.is_mobile else None
        page.window_height = 700 if not self.is_mobile else None

        # Adaptive width for different platforms
        control_width = 400 if not self.is_mobile else 300

        url_input = ft.TextField(
            label="Target URL",
            width=control_width,
            hint_text="https://example.com"
        )

        threads_input = ft.TextField(
            label="Concurrent Threads",
            value="100",
            width=control_width / 2,
            keyboard_type=ft.KeyboardType.NUMBER
        )

        duration_input = ft.TextField(
            label="Duration (seconds)",
            value="30",
            width=control_width / 2,
            keyboard_type=ft.KeyboardType.NUMBER
        )

        method_dropdown = ft.Dropdown(
            width=control_width / 2,
            label="HTTP Method",
            options=[
                ft.dropdown.Option("GET"),
                ft.dropdown.Option("POST"),
                ft.dropdown.Option("HEAD")
            ],
            value="GET"
        )

        use_proxy = ft.Checkbox(label="Use Proxy", value=False)
        proxy_input = ft.TextField(
            label="Proxy URL (http://ip:port)",
            width=control_width,
            visible=False
        )

        status_text = ft.Text("Ready to start...", size=16)
        progress_bar = ft.ProgressBar(width=control_width, visible=False)

        stats_text = ft.Text(size=16)

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

            try:
                threads = int(threads_input.value)
                duration = int(duration_input.value)
            except ValueError:
                status_text.value = "Please enter valid numbers"
                await page.update_async()
                return

            status_text.value = "Test running..."
            progress_bar.visible = True
            await page.update_async()

            proxy = proxy_input.value if use_proxy.value else None

            async def worker():
                while self.stress_test.running:
                    headers = {
                        'User-Agent': random.choice(self.stress_test.user_agents),
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache'
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
            width=control_width,
            on_click=start_test,
            style=ft.ButtonStyle(
                color={
                    ft.MaterialState.DEFAULT: ft.colors.WHITE,
                },
                bgcolor={
                    ft.MaterialState.DEFAULT: ft.colors.BLUE_700,
                    ft.MaterialState.HOVERED: ft.colors.BLUE_800,
                },
            )
        )

        # Создаем контейнер для всех элементов
        content = ft.Column(
            controls=[
                ft.Text(
                    "Web Stress Test Tool",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(
                    content=url_input,
                    padding=ft.padding.only(bottom=10)
                ),
                ft.Row(
                    [threads_input, duration_input],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Container(
                    content=method_dropdown,
                    padding=ft.padding.only(top=10, bottom=10)
                ),
                use_proxy,
                proxy_input,
                ft.Container(
                    content=start_button,
                    padding=ft.padding.only(top=20, bottom=20)
                ),
                status_text,
                progress_bar,
                ft.Container(
                    content=stats_text,
                    padding=ft.padding.only(top=20)
                )
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

        # Добавляем прокрутку для мобильных устройств
        if self.is_mobile:
            page.add(
                ft.Container(
                    content=ft.Column(
                        [content],
                        scroll=ft.ScrollMode.AUTO
                    ),
                    padding=ft.padding.all(20)
                )
            )
        else:
            page.add(
                ft.Container(
                    content=content,
                    padding=ft.padding.all(20)
                )
            )


if __name__ == "__main__":
    app = StressTestGUI()
    ft.app(target=app.main)
