import 'package:ficct_final_app/src/app.dart';
import 'package:ficct_final_app/src/core/utils/frequency_channel.dart';
import 'package:ficct_final_app/src/features/home/presentation/home_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('shows login screen on startup', (WidgetTester tester) async {
    await tester.pumpWidget(const FicctFinalApp());

    expect(find.byType(MaterialApp), findsOneWidget);
    expect(find.text('Inicia sesión'), findsOneWidget);
    expect(find.text('Entrar a WiFiScope'), findsOneWidget);
    expect(find.text('WiFiScope'), findsOneWidget);
  });

  testWidgets('allows access with valid credentials', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(const FicctFinalApp());
    final loginButton = find.widgetWithText(FilledButton, 'Entrar a WiFiScope');

    await tester.enterText(
      find.byType(TextFormField).at(0),
      'demo@wifiscope.app',
    );
    await tester.enterText(find.byType(TextFormField).at(1), 'secure123');
    await tester.ensureVisible(loginButton);
    await tester.tap(loginButton);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 1200));
    await tester.pump(const Duration(milliseconds: 300));
    await tester.pump(const Duration(milliseconds: 300));

    expect(find.byType(HomePage), findsOneWidget);
  });

  testWidgets('shows validation messages for empty login form', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(const FicctFinalApp());
    final loginButton = find.widgetWithText(FilledButton, 'Entrar a WiFiScope');

    await tester.ensureVisible(loginButton);
    await tester.tap(loginButton);
    await tester.pump();

    expect(find.text('Introduce tu correo electrónico.'), findsOneWidget);
    expect(find.text('Introduce tu contraseña.'), findsOneWidget);
  });

  test('maps wifi frequencies to channels', () {
    expect(wifiChannelFromFrequency(2412), 1);
    expect(wifiChannelFromFrequency(2437), 6);
    expect(wifiChannelFromFrequency(2462), 11);
    expect(wifiChannelFromFrequency(5180), 36);
    expect(wifiChannelFromFrequency(5955), 1);
    expect(wifiChannelFromFrequency(1234), isNull);
  });
}
