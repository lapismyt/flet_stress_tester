import flet as ft
import aiohttp
import asyncio
import random
import time
import platform
from typing import Optional
import ssl

# Список реальных User-Agent для разных платформ
USER_AGENTS = [
    # Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Android
    "Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Android 13; Mobile; rv:121.0) Gecko/121.0 Firefox/121.0",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
]


class StressTest:
    def __init__(self):
        self.running = False
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.start_time: Optional[float] = None
        self.last_request_time: Optional[float] = None
        self.response_times = []

    def get_random_user_agent(self):
        return random.choice(USER_AGENTS)

    async def make_request(self, url: str, method: str, headers: dict, proxy: Optional[str] = None):
        start_time = time.time()
        try:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.request(
                        method=method,
                        url=url,
                        headers=headers,
                        proxy=proxy,
                        timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    await response.text()
                    self.successful_requests += 1
                    response_time = time.time() - start_time
                    self.response_times.append(response_time)

        except Exception as e:
            self.failed_requests += 1
        finally:
            self.total_requests += 1
            self.last_request_time = time.time()


class StressTestGUI:
    def __init__(self):
        self.stress_test = StressTest()

    def main(self, page: ft.Page):
        page.title = "Web Stress Tester"
        page.theme_mode = ft.ThemeMode.DARK
        page.window_width = 800
        page.window_height = 900

        # Основные настройки
        url_input = ft.TextField(
            label="Target URL (http:// or https://)",
            width=600,
            text_size=16
        )

        threads_input = ft.TextField(
            label="Concurrent Threads",
            value="100",
            width=200,
            text_size=16
        )

        duration_input = ft.TextField(
            label="Duration (seconds)",
            value="30",
            width=200,
            text_size=16
        )

        method_dropdown = ft.Dropdown(
            width=200,
            label="HTTP Method",
            options=[
                ft.dropdown.Option("GET"),
                ft.dropdown.Option("POST"),
                ft.dropdown.Option("HEAD")
            ],
            value="GET",
            text_size=16
        )

        # Дополнительные настройки
        use_proxy = ft.Checkbox(label="Use Proxy", value=False)
        proxy_input = ft.TextField(
            label="Proxy URL (http://ip:port)",
            width=600,
            visible=False,
            text_size=16
        )

        # Статус и прогресс
        status_text = ft.Text("Ready to start...", size=16, color=ft.colors.GREEN)
        progress_bar = ft.ProgressBar(width=600, visible=False)

        # Статистика
        stats_text = ft.Text(size=16)
        detailed_stats = ft.Text(size=14, color=ft.colors.GREY_400)

        async def update_stats():
            while self.stress_test.running:
                if self.stress_test.start_time:
                    elapsed = time.time() - self.stress_test.start_time
                    rps = self.stress_test.total_requests / elapsed if elapsed > 0 else 0

                    # Основная статистика
                    stats_text.value = (
                        f"✨ Total Requests: {self.stress_test.total_requests}\n"
                        f"✅ Successful: {self.stress_test.successful_requests}\n"
                        f"❌ Failed: {self.stress_test.failed_requests}\n"
                        f"⚡ Requests/sec: {rps:.2f}"
                    )

                    # Детальная статистика
                    if self.stress_test.response_times:
                        avg_response = sum(self.stress_test.response_times) / len(self.stress_test.response_times)
                        min_response = min(self.stress_test.response_times)
                        max_response = max(self.stress_test.response_times)

                        detailed_stats.value = (
                            f"📊 Detailed Statistics:\n"
                            f"Average Response Time: {avg_response:.3f}s\n"
                            f"Min Response Time: {min_response:.3f}s\n"
                            f"Max Response Time: {max_response:.3f}s\n"
                            f"Test Duration: {elapsed:.1f}s"
                        )

                    await page.update_async()
                await asyncio.sleep(0.5)

        async def start_test(e):
            if not url_input.value:
                status_text.value = "⚠️ Please enter a valid URL"
                status_text.color = ft.colors.RED
                await page.update_async()
                return

            self.stress_test = StressTest()
            self.stress_test.running = True
            self.stress_test.start_time = time.time()

            try:
                threads = int(threads_input.value)
                duration = int(duration_input.value)
            except ValueError:
                status_text.value = "⚠️ Invalid thread count or duration"
                status_text.color = ft.colors.RED
                await
