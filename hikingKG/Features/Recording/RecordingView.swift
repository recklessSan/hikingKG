import SwiftUI
import MapKit

struct RecordingView: View {
    @StateObject private var viewModel: RecordingViewModel
    @State private var showAuthAlert = false

    init(track: Track = Track(), locationService: LocationService) {
        _viewModel = StateObject(wrappedValue: RecordingViewModel(track: track, locationService: locationService))
    }

    var body: some View {
        ZStack {
            Map(coordinateRegion: $viewModel.currentRegion,
                showsUserLocation: true,
                userTrackingMode: .constant(.follow))
                .ignoresSafeArea()

            VStack {
                statsCard
                Spacer()
                controls
            }
            .padding()
        }
        .navigationTitle("Запись")
        .navigationBarTitleDisplayMode(.inline)
        .onAppear { ensureAuthorization() }
        .alert("Нужен доступ к геопозиции", isPresented: $showAuthAlert) {
            Button("Отмена", role: .cancel) {}
            Button("Открыть настройки") {
                #if canImport(UIKit)
                if let url = URL(string: UIApplication.openSettingsURLString) {
                    UIApplication.shared.open(url)
                }
                #endif
            }
        } message: {
            Text("Включите геолокацию, чтобы записать трек.")
        }
    }

    private var statsCard: some View {
        HStack {
            statBlock(title: "Время", value: viewModel.elapsedText)
            Divider().frame(height: 36)
            statBlock(title: "Дистанция", value: viewModel.distanceText)
            Divider().frame(height: 36)
            statBlock(title: "Набор", value: viewModel.elevationText)
        }
        .padding()
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 14))
    }

    private func statBlock(title: String, value: String) -> some View {
        VStack(spacing: 2) {
            Text(title).font(.caption).foregroundStyle(.secondary)
            Text(value).font(.headline.monospacedDigit())
        }
        .frame(maxWidth: .infinity)
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(title): \(value)")
    }

    private var controls: some View {
        HStack(spacing: 24) {
            if !viewModel.isRecording {
                Button(action: viewModel.startRecording) {
                    Label("Старт", systemImage: "record.circle")
                        .font(.title3.weight(.semibold))
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .tint(.green)
            } else {
                if viewModel.isPaused {
                    Button(action: viewModel.resumeRecording) {
                        Label("Продолжить", systemImage: "play.fill")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent)
                } else {
                    Button(action: viewModel.pauseRecording) {
                        Label("Пауза", systemImage: "pause.fill")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.bordered)
                }

                Button(role: .destructive, action: viewModel.stopRecording) {
                    Label("Стоп", systemImage: "stop.fill")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .tint(.red)
            }
        }
    }

    private func ensureAuthorization() {
        switch viewModel.locationService.authorizationStatus {
        case .notDetermined:
            viewModel.locationService.requestWhenInUse()
        case .denied, .restricted:
            showAuthAlert = true
        default:
            break
        }
    }
}
