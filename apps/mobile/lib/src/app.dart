import 'package:ficct_final_app/src/core/theme/app_theme.dart';
import 'package:ficct_final_app/src/features/auth/presentation/login_page.dart';
import 'package:ficct_final_app/src/features/home/presentation/home_page.dart';
import 'package:flutter/material.dart';

class FicctFinalApp extends StatefulWidget {
  const FicctFinalApp({super.key});

  @override
  State<FicctFinalApp> createState() => _FicctFinalAppState();
}

class _FicctFinalAppState extends State<FicctFinalApp> {
  LoginResult? _session;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'WiFiScope',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.dark(),
      home: _session == null
          ? LoginPage(
              onLoginSuccess: (result) {
                setState(() {
                  _session = result;
                });
              },
            )
          : HomePage(
              currentUserEmail: _session!.email,
              onLogout: () {
                setState(() {
                  _session = null;
                });
              },
            ),
    );
  }
}
