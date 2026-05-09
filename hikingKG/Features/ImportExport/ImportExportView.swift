import SwiftUI
import UniformTypeIdentifiers

struct ImportExportView: View {
    @State private var showImporter = false
    @State private var lastImportSummary: String?
    @State private var lastError: String?

    var body: some View {
        Form {
            Section("Импорт GPX") {
                Button {
                    showImporter = true
                } label: {
                    Label("Выбрать файл .gpx", systemImage: "tray.and.arrow.down")
                }

                if let lastImportSummary {
                    Text(lastImportSummary).font(.footnote).foregroundStyle(.secondary)
                }
                if let lastError {
                    Text(lastError).font(.footnote).foregroundStyle(.red)
                }
            }

            Section("Экспорт") {
                Text("Экспорт треков выполняется со страницы конкретного трека. См. вкладку «Мои треки».")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }

            Section("Stage 2-4") {
                Text("Полная синхронизация с облачным каталогом, публикация маршрутов и общественные обзоры будут добавлены в последующих стадиях.")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }
        }
        .navigationTitle("Импорт / Экспорт")
        .fileImporter(isPresented: $showImporter,
                      allowedContentTypes: [UTType(filenameExtension: "gpx") ?? .xml],
                      allowsMultipleSelection: false) { result in
            handle(result)
        }
    }

    private func handle(_ result: Result<[URL], Error>) {
        lastError = nil
        lastImportSummary = nil
        do {
            let urls = try result.get()
            guard let url = urls.first else { return }
            let needsStop = url.startAccessingSecurityScopedResource()
            defer { if needsStop { url.stopAccessingSecurityScopedResource() } }

            let importer = GPXImporter()
            let parsed = try importer.importTrack(from: url)

            var track = Track()
            track.title = parsed.name ?? url.deletingPathExtension().lastPathComponent
            track.points = parsed.trackPoints
            track.status = .stopped
            track.createdAt = Date()
            track.gpxLocalFilename = url.lastPathComponent
            LocalStorageService.shared.saveTrack(track)
            lastImportSummary = "Импортирован трек: \(track.title ?? "—") (точек: \(track.points.count))"
        } catch {
            lastError = "Не удалось импортировать GPX: \(error.localizedDescription)"
        }
    }
}
