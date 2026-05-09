# MVP — фундамент платформы для походов по Кыргызстану

Этот документ описывает MVP-фундамент проекта `hikingKG`, реализованный в этом
PR. Он покрывает только Stage 1: каталог, запись трека, базовый импорт/экспорт
GPX и навигацию приложения. Сетевой backend, аутентификация, синхронизация и
сообщество — стадии 2–4.

## Что входит в MVP

### Структура и точка входа
- Удалён пустой файл-заготовка `App/HikingKGApp.swift`, чтобы остался
  единственный `@main` — `hikingKG/hikingKGApp.swift`.
- Удалён конфликтующий пустой `Features/Recording/LocationService.swift`;
  единый рабочий сервис — `Features/Common/Services/LocationService.swift`.
- `ContentView` теперь просто оборачивает `RootTabView` (4 вкладки).

### Модели (`Features/Common/Models`)
- `User`
- `Region` (slug, локализованные имена, координаты центра)
- `Route` (поля: title, summary, description, regionSlug, difficulty,
  distanceKm, elevationGainM, durationHours, seasonFrom/To, start/end
  координаты, gpxUrl, gpxLocalFilename, photos, pois, tags,
  isOfflineAvailable, isPublic, createdBy)
- `RoutePhoto`, `Tag`, `Poi`
- `Track` (поля: routeId, userId, title, description, region, points,
  status, startedAt, finishedAt, distanceKm, durationSeconds,
  elevationGainM, pointsCount, gpxUrl, gpxLocalFilename, createdAt)
- `TrackPoint`, `TrackStatus`
- `Review`, `Report`

### Каталог Кыргызстана (`CatalogService`)
Содержит 8 регионов и 9 базовых маршрутов:
- Ala Archa (Ак-Сай водопад, Ак-Сай ледник)
- Karakol / Issyk-Kul (Ала-Кёль)
- Naryn (Кель-Суу)
- Song-Kul (северный берег)
- Alay (БЛ Пика Ленина)
- Jyrgalan (Боз-Учук)
- Arslanbob (водопады)
- Kyrgyz Nomad Trail (секция Сон-Куль ↔ Каракол)

Поиск (`CatalogService.search`) поддерживает фильтрацию по строке, региону и
сложности.

### UI (`Features/...`)
- `RootTabView` — четыре вкладки: Маршруты, Запись, Треки, Импорт.
- `RouteCatalogView` — список с поиском (`.searchable`), фильтрами по
  региону и сложности.
- `RouteDetailView` — статистика, теги, сезон, описание, мини-карта.
- `RecordingView` + `RecordingViewModel` — карта + плитка статистики
  (время/дистанция/набор) + кнопки Старт / Пауза / Продолжить / Стоп.
- `TrackListView` + `TrackListViewModel` — список локальных треков.
- `TrackDetailView` + `TrackDetailViewModel` — детали трека + экспорт GPX.
- `ImportExportView` — импорт `.gpx` через `.fileImporter`.
- Общие `EmptyStateView`, `ConfirmDialog`, `RouteMapView`.

### Сервисы
- `LocationService` — `@MainActor`, `nonisolated` делегатные методы
  CoreLocation, корректный запрос разрешений, включение
  `allowsBackgroundLocationUpdates` только при `authorizedAlways`.
- `RecordingViewModel` — корректное накопление времени между Pause/Resume,
  обновление дистанции по последней точке, фиксация `durationSeconds` по
  Stop, защита от добавления точек в паузе.
- `LocalStorageService` — JSON в `UserDefaults` (упрощение для MVP).
- `CatalogService` — синглтон, отдаёт seed-данные.

### GPX
- `GPXImporter` использует `XMLParser` + делегат: парсит `trkpt`, `wpt`,
  `rtept`, `ele`, `time`. Возвращает массив `TrackPoint`, точки интереса и
  имя.
- `GPXExporter` сериализует `Track` в GPX 1.1 (trk/trkseg/trkpt с ele/time)
  и waypoints для `Route`.

### Privacy / background (Xcode build settings)
В `project.pbxproj` для конфигураций Debug и Release добавлены ключи
`INFOPLIST_KEY_*`:
- `NSLocationWhenInUseUsageDescription`
- `NSLocationAlwaysAndWhenInUseUsageDescription`
- `NSPhotoLibraryUsageDescription`
- `NSPhotoLibraryAddUsageDescription`
- `NSCameraUsageDescription`
- `UIBackgroundModes = "location"`

(Отдельный `Info.plist` не используется — проект на `GENERATE_INFOPLIST_FILE`.)

## Что НЕ входит в MVP (Stage 2–4)

- Аккаунты и аутентификация (Sign in with Apple / email).
- Облачное хранилище маршрутов и треков (REST/GraphQL backend).
- Загрузка фотографий, точек интереса, отчётов от пользователей.
- Социальный слой: лайки, комментарии, рейтинг, отчёты модерации.
- Полноценная локализация (RU/KY/EN) и контент-менеджмент.
- Офлайн-карты (тайлы), автономная маршрутизация, навигация по маршруту.
- Уведомления, бэкенд push, миграция данных в CoreData/SQLite/SwiftData.
- Полноценная политика приватности и согласие на обработку.
- E2E и UI-тесты, CI.

## Шаги верификации в Xcode (на macOS)

Linux в этом окружении не может собрать iOS-приложение. Чтобы проверить
изменения локально:

1. Открыть `hikingKG.xcodeproj` в Xcode 16 или новее.
2. Выбрать схему `hikingKG`, симулятор iPhone 15 (iOS 17+).
3. `Product → Clean Build Folder`.
4. `Product → Build` — убедиться, что билд проходит.
5. `Product → Run` — запустить на симуляторе и проверить:
   - вкладка «Маршруты» открывает список с фильтрами и поиском;
   - детальная страница маршрута показывает карту, статистику, теги,
     сезон;
   - вкладка «Запись» запрашивает разрешение на геолокацию (симулятор —
     `Features → Location → City Run`), Старт/Пауза/Стоп переключают
     состояние, появляется живая дистанция;
   - после Stop трек появляется во вкладке «Треки», открывается деталь,
     работает «Экспорт GPX»;
   - вкладка «Импорт» открывает системный picker для `.gpx`.
6. Проверить, что `Info.plist` (генерируется) содержит описанные выше ключи
   (`Build → Show Build Folder → Products → Info.plist`).

## Известные ограничения

- Хранилище — `UserDefaults` (для MVP допустимо, но требует миграции в
  Stage 2).
- Сезон — простые `Season` enum (1..12); диапазон не поддерживает
  «зимние» сезоны через декабрь→февраль.
- Поиск работает только по `title`, `summary`, тегам.
- Нет прогресса/процента выполнения маршрута во время записи.
- В симуляторе фоновая геолокация ограничена; реальное поведение проверять
  на устройстве.
