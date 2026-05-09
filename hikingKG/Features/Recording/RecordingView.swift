// Features/Recording/RecordingView.swift

import SwiftUI
import MapKit

struct RecordingView: View {
    @StateObject private var viewModel: RecordingViewModel
    @State private var showAuthAlert = false
    
    init(track: Track, locationService: LocationService) {
        _viewModel = StateObject(wrappedValue: RecordingViewModel(track: track, locationService: locationService))
    }
    
    var body: some View {
        ZStack {
            mapViewOverlay
            
            overlayControls
            
            if viewModel.track.points.isEmpty && !viewModel.isRecording {
                startHint
            }
        }
        .onAppear {
            checkAuthorization()
        }
        .alert("Location Access Required", isPresented: $showAuthAlert) {
            Button("OK", role: .cancel) { }
            Button("Settings") {
                if let url = URL(string: UIApplication.openSettingsURLString) {
                    UIApplication.shared.open(url)
                }
            }
        } message: {
            Text("Please enable Location Services to record your hiking track.")
        }
    }
    
    // MARK: - Map
    
    private var mapViewOverlay: some View {
        Map(coordinateRegion: $viewModel.currentRegion,
            showsUserLocation: true,
            userTrackingMode: .constant(.follow))
    }
    
    // MARK: - Controls
    
    private var overlayControls: some View {
        VStack {
            HStack {
                Text(viewModel.startTimeText)
                    .font(.title2.monospacedDigit())
                    .fontWeight(.semibold)
                Spacer()
                Text(viewModel.distanceText)
                    .fontWeight(.semibold)
                Spacer()
                Text(viewModel.elevationText)
                    .fontWeight(.semibold)
            }
            .padding()
            .frame(maxWidth: .infinity)
            .background(.ultraThinMaterial)
            .cornerRadius(12)
            .padding()
            
            Spacer()
            
            HStack(spacing: 24) {
                if viewModel.isRecording {
                    Button(action: pauseRecording) {
                        Image(systemName: "pause.fill")
                            .font(.title2)
                            .frame(width: 60, height: 60)
                            .background(Color.red.opacity(0.2))
                            .clipShape(Circle())
                    }
                    
                    Button(action: stopRecording) {
                        Image(systemName: "square.fill")
                            .font(.title2)
                            .frame(width: 60, height: 60)
                            .background(Color.red.opacity(0.2))
                            .clipShape(Circle())
                    }
                } else {
                    Button(action: startRecording) {
                        Image(systemName: "record.circle")
                            .font(.title2)
                            .frame(width: 70, height: 70)
                            .background(Color.green.opacity(0.25))
                            .clipShape(Circle())
                    }
                }
            }
            .padding()
        }
    }
    
    // MARK: - Hint
    
    private var startHint: some View {
        VStack {
            Spacer()
            Text("Press the green button to start recording your track")
                .multilineTextAlignment(.center)
                .padding(16)
                .background(.ultraThinMaterial)
                .cornerRadius(12)
                .padding()
        }
    }
    
    // MARK: - Logic
    
    private func checkAuthorization() {
        switch viewModel.locationService.authorizationStatus {
        case .notDetermined:
            viewModel.locationService.requestWhenInUse()
        case .denied, .restricted:
            showAuthAlert = true
        default:
            break
        }
    }
    
    private func startRecording()

