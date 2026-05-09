import SwiftUI

struct RouteCatalogView: View {
    @StateObject private var catalog = CatalogService.shared
    @State private var query: String = ""
    @State private var selectedRegion: Region?
    @State private var selectedDifficulty: RouteDifficulty?

    var body: some View {
        List {
            Section {
                regionPicker
                difficultyPicker
            }

            if filteredRoutes.isEmpty {
                Section {
                    EmptyStateView(systemImage: "magnifyingglass",
                                   title: "Ничего не найдено",
                                   message: "Попробуйте изменить фильтры или поисковый запрос.")
                        .listRowBackground(Color.clear)
                }
            } else {
                Section("Маршруты") {
                    ForEach(filteredRoutes) { route in
                        NavigationLink(value: route) {
                            RouteRow(route: route, region: catalog.region(for: route.regionSlug))
                        }
                    }
                }
            }
        }
        .searchable(text: $query, prompt: "Найти маршрут")
        .navigationTitle("Маршруты КР")
        .navigationDestination(for: Route.self) { route in
            RouteDetailView(route: route)
        }
    }

    private var filteredRoutes: [Route] {
        catalog.search(query: query,
                       difficulty: selectedDifficulty,
                       regionSlug: selectedRegion?.slug)
    }

    private var regionPicker: some View {
        Picker("Регион", selection: $selectedRegion) {
            Text("Все регионы").tag(Region?.none)
            ForEach(catalog.regions) { region in
                Text(region.nameRu ?? region.name).tag(Optional(region))
            }
        }
    }

    private var difficultyPicker: some View {
        Picker("Сложность", selection: $selectedDifficulty) {
            Text("Любая").tag(RouteDifficulty?.none)
            ForEach(RouteDifficulty.allCases) { difficulty in
                Text(difficulty.titleRu).tag(Optional(difficulty))
            }
        }
    }
}

private struct RouteRow: View {
    let route: Route
    let region: Region?

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(route.title).font(.headline)
            if let region {
                Text(region.nameRu ?? region.name)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            HStack(spacing: 12) {
                Label(String(format: "%.0f км", route.distanceKm), systemImage: "ruler")
                Label(route.difficulty.titleRu, systemImage: "figure.hiking")
                Label(String(format: "+%.0f м", route.elevationGainM), systemImage: "arrow.up.right")
            }
            .font(.caption)
            .foregroundStyle(.secondary)
        }
        .padding(.vertical, 4)
    }
}
