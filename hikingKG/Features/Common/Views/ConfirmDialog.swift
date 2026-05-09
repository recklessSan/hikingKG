import SwiftUI

struct ConfirmDialog: ViewModifier {
    @Binding var isPresented: Bool
    let title: String
    let message: String
    let confirmTitle: String
    let onConfirm: () -> Void

    func body(content: Content) -> some View {
        content.confirmationDialog(title, isPresented: $isPresented, titleVisibility: .visible) {
            Button(confirmTitle, role: .destructive, action: onConfirm)
            Button("Отмена", role: .cancel) {}
        } message: {
            Text(message)
        }
    }
}

extension View {
    func confirmDialog(isPresented: Binding<Bool>,
                       title: String,
                       message: String,
                       confirmTitle: String = "Подтвердить",
                       onConfirm: @escaping () -> Void) -> some View {
        modifier(ConfirmDialog(isPresented: isPresented,
                               title: title,
                               message: message,
                               confirmTitle: confirmTitle,
                               onConfirm: onConfirm))
    }
}
