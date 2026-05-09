import SwiftUI
import CoreLocation

struct RouteDetailView: View {
    let route: Route
    @StateObject private var catalog = CatalogService.shared

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                RouteMapView(coordinates: [route.startCoordinate, route.endCoordinate],
                             startCoordinate: route.startCoordinate,
                             endCoordinate: route.endCoordinate)
                    .frame(height: 240)
                    .clipShape(RoundedRectangle(cornerRadius: 12))

                Text(route.title).font(.title.bold())

                if let region = catalog.region(for: route.regionSlug) {
                    Label(region.nameRu ?? region.name, systemImage: "mappin.circle")
                        .foregroundStyle(.secondary)
                }

                Text(route.summary)
                    .font(.body)

                statsGrid

                if !route.tags.isEmpty {
                    tagsView
                }

                seasonView

                Text(route.description)
                    .font(.body)

                if route.isOfflineAvailable {
                    Label("Доступен офлайн", systemImage: "icloud.and.arrow.down")
                        .foregroundStyle(.green)
                }
            }
            .padding()
        }
        .navigationTitle(route.title)
        .navigationBarTitleDisplayMode(.inline)
    }

    private var statsGrid: some View {
        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
            statCard(title: "Дистанция", value: String(format: "%.1f км", route.distanceKm))
            statCard(title: "Сложность", value: route.difficulty.titleRu)
            statCard(title: "Набор", value: String(format: "+%.0f м", route.elevationGainM))
            statCard(title: "Время", value: String(format: "≈ %.0f ч", route.durationHours))
        }
    }

    private func statCard(title: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title).font(.caption).foregroundStyle(.secondary)
            Text(value).font(.headline)
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
    }

    private var tagsView: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(route.tags, id: \.id) { tag in
                    Text(tag.title)
                        .font(.caption)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 6)
                        .background(.thinMaterial, in: Capsule())
                }
            }
        }
    }

    private var seasonView: some View {
        Label("Сезон: \(monthName(route.seasonFrom)) – \(monthName(route.seasonTo))",
              systemImage: "calendar")
            .font(.subheadline)
            .foregroundStyle(.secondary)
    }

    private func monthName(_ season: Season) -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "ru_RU")
        return formatter.standaloneMonthSymbols[season.rawValue - 1].capitalized
    }
}
