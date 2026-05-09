import SwiftUI

struct EmptyStateView: View {
    let systemImage: String
    let title: String
    let message: String

    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: systemImage)
                .font(.system(size: 48))
                .foregroundStyle(.secondary)
            Text(title).font(.headline)
            Text(message)
                .font(.subheadline)
                .multilineTextAlignment(.center)
                .foregroundStyle(.secondary)
        }
        .padding()
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .accessibilityElement(children: .combine)
    }
}
