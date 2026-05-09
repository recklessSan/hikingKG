import SwiftUI

struct RootTabView: View {
    @StateObject private var locationService = LocationService()

    var body: some View {
        TabView {
            NavigationStack {
                RouteCatalogView()
            }
            .tabItem {
                Label("Маршруты", systemImage: "map")
            }

            NavigationStack {
                RecordingView(track: Track(), locationService: locationService)
            }
            .tabItem {
                Label("Запись", systemImage: "record.circle")
            }

            NavigationStack {
                TrackListView()
            }
            .tabItem {
                Label("Треки", systemImage: "figure.hiking")
            }

            NavigationStack {
                ImportExportView()
            }
            .tabItem {
                Label("Импорт", systemImage: "square.and.arrow.down.on.square")
            }
        }
        .environmentObject(locationService)
    }
}
