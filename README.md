# VPN Deck

Плагин для Decky Loader, позволяющий управлять VPN соединением через AmneziaWG на Steam Deck.

## 📋 Описание

**VPN Deck** — это плагин для Decky Loader, который предоставляет удобный интерфейс для управления VPN соединением через AmneziaWG прямо из игрового режима Steam Deck. Плагин позволяет:

- Включать и выключать VPN соединение одним нажатием
- Отслеживать статус VPN соединения в реальном времени
- Просматривать историю ошибок и диагностическую информацию
- Управлять VPN без необходимости выхода из игрового режима

Плагин требует root-доступ для работы с системными сервисами VPN.

### ⚠️ Важно: Ограничения плагина

**Плагин только управляет интерфейсом `awg0` через `systemctl`** — он поднимает и останавливает уже настроенный VPN интерфейс. 

**Сам VPN AmneziaWG необходимо настроить самостоятельно в Desktop Mode:**
- Соберите из исходников [amneziawg-go](https://github.com/amnezia-vpn/amneziawg-go) и [amneziawg-tools](https://github.com/amnezia-vpn/amneziawg-tools)
- Настройте VPN конфигурацию
- Убедитесь, что сервис `awg0` корректно настроен и может быть управляем через `systemctl`

Плагин не выполняет первоначальную настройку VPN — он только управляет уже настроенным соединением.

#### Сборка AmneziaWG библиотек

Для работы плагина необходимо собрать и установить две библиотеки:

**1. amneziawg-go** ([репозиторий](https://github.com/amnezia-vpn/amneziawg-go))

```bash
# Клонируйте репозиторий
git clone https://github.com/amnezia-vpn/amneziawg-go
cd amneziawg-go

# Соберите (требуется Go)
make

# Установите (обычно требует sudo)
sudo make install
```

**2. amneziawg-tools** ([репозиторий](https://github.com/amnezia-vpn/amneziawg-tools))

```bash
# Клонируйте репозиторий
git clone https://github.com/amnezia-vpn/amneziawg-tools
cd amneziawg-tools

# Перейдите в директорию с исходниками
cd src

# Соберите (требуется C компилятор)
make

# Установите (обычно требует sudo)
sudo make install
```

После установки обеих библиотек настройте VPN конфигурацию и создайте systemd сервис для управления интерфейсом `awg0`.

## 🛠️ Установка зависимостей и подготовка проекта

### Требования

- **Node.js** (рекомендуется версия 18 или выше)
- **pnpm** (менеджер пакетов)
- **Python 3** (для бэкенда плагина)
- **Docker** (должен быть установлен и запущен - используется Decky CLI для сборки плагина)
- **Git**

### Установка зависимостей

1. **Клонируйте репозиторий:**
   ```bash
   git clone <repository-url>
   cd vpn-deck
   ```

2. **Установите pnpm** (если еще не установлен):
   ```bash
   npm install -g pnpm
   ```

3. **Установите зависимости проекта:**
   ```bash
   pnpm install
   ```

4. **Установите Decky CLI** (необходимо для сборки плагина):
   
   CLI будет автоматически установлен при первом запуске скрипта сборки, или вы можете установить его вручную:
   
   ```bash
   # Создайте директорию для CLI
   mkdir -p cli
   
   # Скачайте Decky CLI для вашей платформы
   # Для macOS (x86_64):
   curl -L -o cli/decky https://github.com/SteamDeckHomebrew/cli/releases/latest/download/decky-macOS-x86_64
   
   # Для macOS (ARM64):
   curl -L -o cli/decky https://github.com/SteamDeckHomebrew/cli/releases/latest/download/decky-macOS-aarch64
   
   # Для Linux (x86_64):
   curl -L -o cli/decky https://github.com/SteamDeckHomebrew/cli/releases/latest/download/decky-linux-x86_64
   
   # Для Linux (ARM64):
   curl -L -o cli/decky https://github.com/SteamDeckHomebrew/cli/releases/latest/download/decky-linux-aarch64
   
   # Сделайте файл исполняемым
   chmod +x cli/decky
   ```

## 🔨 Сборка проекта

### Сборка для продакшена

**⚠️ Важно:** Перед сборкой убедитесь, что Docker запущен и работает. Decky CLI использует Docker для сборки плагина в изолированном окружении.

1. **Проверьте, что Docker запущен:**
   ```bash
   docker ps
   ```
   Если Docker не запущен, запустите его (например, через Docker Desktop).

2. **Соберите фронтенд:**
   ```bash
   pnpm build
   ```

3. **Соберите плагин в ZIP файл:**
   ```bash
   ./cli/decky plugin build
   ```
   
   Decky CLI соберет плагин в Docker образе и выведет результат в директорию `./out`. Готовый плагин будет находиться в `out/vpn-deck.zip`

### Установка на Steam Deck

1. Скопируйте файл `out/vpn-deck.zip` на ваш Steam Deck
2. Откройте Decky Loader в игровом режиме
3. Перейдите в настройки плагинов
4. Установите плагин из ZIP файла

## 🚀 Релизинг

Проект использует [release-it](https://github.com/release-it/release-it) для автоматического создания релизов.

### Подготовка к релизу

1. **Убедитесь, что вы на ветке `main`:**
   ```bash
   git branch --show-current
   ```

2. **Убедитесь, что все изменения закоммичены:**
   ```bash
   git status
   ```

3. **Убедитесь, что у вас настроен GitHub CLI и вы авторизованы:**
   ```bash
   gh auth status
   # Если не авторизованы:
   gh auth login
   ```

### Создание релиза

#### Интерактивный режим (рекомендуется)

```bash
pnpm release
```

Release-it предложит выбрать тип версии и покажет предварительный просмотр изменений.

#### Прямое указание типа версии

```bash
# Patch релиз (1.0.0 → 1.0.1) - для исправлений багов
pnpm release:patch

# Minor релиз (1.0.0 → 1.1.0) - для новой функциональности
pnpm release:minor

# Major релиз (1.0.0 → 2.0.0) - для критических изменений
pnpm release:major
```

## 📝 Лицензия

BSD-3-Clause

## 🤝 Вклад в проект

Вклад в проект приветствуется! Пожалуйста, создавайте issues и pull requests.

## 📞 Поддержка

Если у вас возникли проблемы или вопросы:

1. Проверьте [Issues](https://github.com/mrwaip/vpn-deck/issues)
2. Создайте новый Issue с описанием проблемы
3. Убедитесь, что вы предоставили достаточно информации для воспроизведения проблемы
