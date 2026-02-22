#!/bin/bash
# Quick reference для тестирования GitHub Actions workflow

cat << 'EOF'
╔══════════════════════════════════════════════════════════════════╗
║          🧪 ТЕСТИРОВАНИЕ GITHUB ACTIONS WORKFLOW                 ║
╚══════════════════════════════════════════════════════════════════╝

📋 ТЕКУЩАЯ КОНФИГУРАЦИЯ:
   ✅ workflow_dispatch - ручной запуск (ВКЛЮЧЕН)
   ✅ pull_request - авто на PR (ВКЛЮЧЕН)
   ❌ push на main - автоматический запуск (ОТКЛЮЧЕН)

🚀 БЫСТРЫЙ СТАРТ:

1️⃣  Ручной запуск на текущей ветке:
    gh workflow run build-binaries.yml

2️⃣  Ручной запуск на конкретной ветке:
    gh workflow run build-binaries.yml --ref v2

3️⃣  С debug режимом:
    gh workflow run build-binaries.yml --ref v2 -f debug=true

4️⃣  Смотреть статус:
    gh run list --workflow=build-binaries.yml
    gh run watch

5️⃣  Скачать результат:
    gh run download --name amneziawg-binaries-steamos-amd64

📖 ПОЛНАЯ ДОКУМЕНТАЦИЯ:
   См. TESTING_WORKFLOW.md

🔧 ТЕСТИРОВАНИЕ НА FEATURE BRANCH:

   git checkout -b test/ci
   git push origin test/ci
   gh workflow run build-binaries.yml --ref test/ci
   gh run watch

✅ РЕКОМЕНДУЕМЫЙ WORKFLOW:
   1. Создать feature branch
   2. Запустить workflow вручную на этой ветке
   3. Проверить результат
   4. После успеха - мердж в main

EOF
