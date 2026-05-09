import Foundation

final class CatalogService: ObservableObject {
    static let shared = CatalogService()

    @Published private(set) var regions: [Region]
    @Published private(set) var routes: [Route]

    private init() {
        self.regions = CatalogService.makeRegions()
        self.routes = CatalogService.makeRoutes()
    }

    func region(for slug: String) -> Region? {
        regions.first { $0.slug == slug }
    }

    func routes(in regionSlug: String) -> [Route] {
        routes.filter { $0.regionSlug == regionSlug }
    }

    func search(query: String,
                difficulty: RouteDifficulty? = nil,
                regionSlug: String? = nil) -> [Route] {
        let normalized = query.lowercased().trimmingCharacters(in: .whitespacesAndNewlines)
        return routes.filter { route in
            if let regionSlug, route.regionSlug != regionSlug { return false }
            if let difficulty, route.difficulty != difficulty { return false }
            if normalized.isEmpty { return true }
            return route.title.lowercased().contains(normalized)
                || route.summary.lowercased().contains(normalized)
                || route.tags.contains { $0.title.lowercased().contains(normalized) }
        }
    }

    // MARK: - Seed regions (Kyrgyzstan)

    private static func makeRegions() -> [Region] {
        [
            Region(slug: "ala-archa",
                   name: "Ala Archa",
                   nameRu: "Ала-Арча",
                   nameKy: "Ала-Арча",
                   summary: "Национальный парк рядом с Бишкеком: альпийские долины, ледники, водопады.",
                   centerLatitude: 42.5631,
                   centerLongitude: 74.4843,
                   coverAssetName: "region_ala_archa"),
            Region(slug: "karakol-issyk-kul",
                   name: "Karakol / Issyk-Kul",
                   nameRu: "Каракол и Иссык-Куль",
                   nameKy: "Каракол / Ысык-Көл",
                   summary: "Хребет Терскей Ала-Тоо, озёра, тёплое озеро Иссык-Куль.",
                   centerLatitude: 42.4907,
                   centerLongitude: 78.3936,
                   coverAssetName: "region_karakol"),
            Region(slug: "naryn",
                   name: "Naryn",
                   nameRu: "Нарын",
                   nameKy: "Нарын",
                   summary: "Высокогорные плато, сырты, традиционная пастбищная культура.",
                   centerLatitude: 41.4287,
                   centerLongitude: 75.9911,
                   coverAssetName: "region_naryn"),
            Region(slug: "song-kul",
                   name: "Song-Kul",
                   nameRu: "Сон-Куль",
                   nameKy: "Соң-Көл",
                   summary: "Высокогорное озеро на высоте более 3000 м, юрточные лагеря.",
                   centerLatitude: 41.8475,
                   centerLongitude: 75.1094,
                   coverAssetName: "region_song_kul"),
            Region(slug: "alay",
                   name: "Alay",
                   nameRu: "Алай",
                   nameKy: "Алай",
                   summary: "Памиро-Алайский высокогорный регион, виды на Пик Ленина.",
                   centerLatitude: 39.5667,
                   centerLongitude: 72.9333,
                   coverAssetName: "region_alay"),
            Region(slug: "jyrgalan",
                   name: "Jyrgalan",
                   nameRu: "Джыргалан",
                   nameKy: "Жыргалаң",
                   summary: "Развивающийся горный кластер на востоке Иссык-Кульской области.",
                   centerLatitude: 42.6486,
                   centerLongitude: 79.0986,
                   coverAssetName: "region_jyrgalan"),
            Region(slug: "arslanbob",
                   name: "Arslanbob",
                   nameRu: "Арсланбоб",
                   nameKy: "Арстанбап",
                   summary: "Крупнейший в мире реликтовый ореховый лес и водопады в Джалал-Абаде.",
                   centerLatitude: 41.3370,
                   centerLongitude: 72.9374,
                   coverAssetName: "region_arslanbob"),
            Region(slug: "kyrgyz-nomad-trail",
                   name: "Kyrgyz Nomad Trail",
                   nameRu: "Маршрут кочевников",
                   nameKy: "Көчмөн жолу",
                   summary: "Многодневный сквозной трек, объединяющий ключевые горные регионы страны.",
                   centerLatitude: 41.9000,
                   centerLongitude: 74.6900,
                   coverAssetName: "region_nomad_trail")
        ]
    }

    // MARK: - Seed routes

    private static func makeRoutes() -> [Route] {
        let waterfallTag = Tag(slug: "waterfall", title: "Водопад")
        let glacierTag = Tag(slug: "glacier", title: "Ледник")
        let lakeTag = Tag(slug: "lake", title: "Озеро")
        let yurtTag = Tag(slug: "yurts", title: "Юрты")
        let multidayTag = Tag(slug: "multiday", title: "Многодневный")
        let familyTag = Tag(slug: "family", title: "Для семьи")

        return [
            Route(
                title: "Водопад Ак-Сай",
                summary: "Короткий радиальный маршрут к водопаду в Ала-Арче.",
                description: "Тропа идёт через хвойный лес и переходит на каменистый склон. Подходит для подготовленных туристов на день.",
                regionSlug: "ala-archa",
                difficulty: .moderate,
                distanceKm: 9.0,
                elevationGainM: 850,
                durationHours: 6,
                seasonFrom: .may,
                seasonTo: .october,
                startLatitude: 42.5631, startLongitude: 74.4843,
                endLatitude: 42.5310, endLongitude: 74.4990,
                gpxLocalFilename: "ak_sai_waterfall.gpx",
                tags: [waterfallTag]
            ),
            Route(
                title: "Ледник Ак-Сай",
                summary: "Радиалка к языку ледника, требует акклиматизации.",
                description: "Подъём по морене до высоты ~3700 м. Альпийская погода, требуются мембрана и треккинговые палки.",
                regionSlug: "ala-archa",
                difficulty: .hard,
                distanceKm: 16.0,
                elevationGainM: 1700,
                durationHours: 11,
                seasonFrom: .june,
                seasonTo: .september,
                startLatitude: 42.5631, startLongitude: 74.4843,
                endLatitude: 42.5050, endLongitude: 74.5200,
                gpxLocalFilename: "ak_sai_glacier.gpx",
                tags: [glacierTag]
            ),
            Route(
                title: "Каракол — Ала-Кёль",
                summary: "Классический трек к высокогорному озеру Ала-Кёль.",
                description: "2–3 дня. Подъём через долину Каракол, ночёвка у озера, перевал Ала-Кёль (3860 м), спуск к Алтын-Арашану.",
                regionSlug: "karakol-issyk-kul",
                difficulty: .hard,
                distanceKm: 42.0,
                elevationGainM: 2400,
                durationHours: 22,
                seasonFrom: .july,
                seasonTo: .september,
                startLatitude: 42.5040, startLongitude: 78.4640,
                endLatitude: 42.5230, endLongitude: 78.6100,
                gpxLocalFilename: "ala_kol_pass.gpx",
                tags: [lakeTag, multidayTag]
            ),
            Route(
                title: "Кель-Суу",
                summary: "Удалённое горное озеро у границы с Китаем.",
                description: "Доступ через погранзону. Однодневный треккинг от лагеря у юрт.",
                regionSlug: "naryn",
                difficulty: .moderate,
                distanceKm: 12.0,
                elevationGainM: 600,
                durationHours: 7,
                seasonFrom: .july,
                seasonTo: .september,
                startLatitude: 40.6950, startLongitude: 76.6610,
                endLatitude: 40.6770, endLongitude: 76.6800,
                gpxLocalFilename: "kel_suu.gpx",
                tags: [lakeTag]
            ),
            Route(
                title: "Сон-Куль — северный берег",
                summary: "Лёгкая прогулка по плато вокруг озера Сон-Куль.",
                description: "Подходит для семей, юрточные лагеря по дороге, лошади, кумыс.",
                regionSlug: "song-kul",
                difficulty: .easy,
                distanceKm: 14.0,
                elevationGainM: 250,
                durationHours: 5,
                seasonFrom: .june,
                seasonTo: .september,
                startLatitude: 41.8650, startLongitude: 75.0930,
                endLatitude: 41.8350, endLongitude: 75.1530,
                gpxLocalFilename: "song_kul_north.gpx",
                tags: [lakeTag, yurtTag, familyTag]
            ),
            Route(
                title: "Базовый лагерь Пика Ленина",
                summary: "Трек к базовому лагерю на 3600 м.",
                description: "Несколько дней с акклиматизацией. Виды на семитысячник.",
                regionSlug: "alay",
                difficulty: .expert,
                distanceKm: 28.0,
                elevationGainM: 1500,
                durationHours: 18,
                seasonFrom: .july,
                seasonTo: .august,
                startLatitude: 39.5950, startLongitude: 72.8520,
                endLatitude: 39.4180, endLongitude: 72.9000,
                gpxLocalFilename: "lenin_bc.gpx",
                tags: [glacierTag, multidayTag]
            ),
            Route(
                title: "Джыргалан — Боз-Учук",
                summary: "Однодневный трек по альпийским пастбищам.",
                description: "Тропа поднимается на гребень с видами на Иссык-Куль.",
                regionSlug: "jyrgalan",
                difficulty: .moderate,
                distanceKm: 18.0,
                elevationGainM: 1100,
                durationHours: 8,
                seasonFrom: .june,
                seasonTo: .october,
                startLatitude: 42.6486, startLongitude: 79.0986,
                endLatitude: 42.6750, endLongitude: 79.1500,
                gpxLocalFilename: "jyrgalan_boz_uchuk.gpx",
                tags: [yurtTag]
            ),
            Route(
                title: "Водопады Арсланбоба",
                summary: "Маршрут к большому и малому водопадам.",
                description: "Тропа сквозь ореховые леса, легко доступная для семей.",
                regionSlug: "arslanbob",
                difficulty: .easy,
                distanceKm: 6.0,
                elevationGainM: 400,
                durationHours: 4,
                seasonFrom: .april,
                seasonTo: .november,
                startLatitude: 41.3370, startLongitude: 72.9374,
                endLatitude: 41.3500, endLongitude: 72.9300,
                gpxLocalFilename: "arslanbob_falls.gpx",
                tags: [waterfallTag, familyTag]
            ),
            Route(
                title: "Kyrgyz Nomad Trail — секция Сон-Куль ↔ Каракол",
                summary: "Магистральная секция многодневного маршрута.",
                description: "Многодневный сквозной переход с использованием юрт и сельских гостевых домов.",
                regionSlug: "kyrgyz-nomad-trail",
                difficulty: .hard,
                distanceKm: 120.0,
                elevationGainM: 5200,
                durationHours: 60,
                seasonFrom: .july,
                seasonTo: .september,
                startLatitude: 41.8475, startLongitude: 75.1094,
                endLatitude: 42.4907, endLongitude: 78.3936,
                gpxLocalFilename: "knt_song_kul_karakol.gpx",
                tags: [multidayTag, yurtTag]
            )
        ]
    }
}
