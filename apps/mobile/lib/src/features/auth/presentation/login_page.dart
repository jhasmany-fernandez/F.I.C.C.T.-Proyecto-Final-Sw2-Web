import 'dart:async';

import 'package:ficct_final_app/src/core/config/app_config.dart';
import 'package:ficct_final_app/src/core/theme/app_theme.dart';
import 'package:flutter/material.dart';

class LoginPage extends StatefulWidget {
  const LoginPage({required this.onLoginSuccess, super.key});

  final ValueChanged<LoginResult> onLoginSuccess;

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  bool _obscurePassword = true;
  bool _rememberSession = true;
  bool _isSubmitting = false;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final form = _formKey.currentState;
    if (form == null || !form.validate()) {
      return;
    }

    setState(() {
      _isSubmitting = true;
    });

    await Future<void>.delayed(const Duration(milliseconds: 1100));

    if (!mounted) {
      return;
    }

    setState(() {
      _isSubmitting = false;
    });

    widget.onLoginSuccess(
      LoginResult(
        email: _emailController.text.trim(),
        rememberSession: _rememberSession,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      body: DecoratedBox(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFF061110), Color(0xFF071715), Color(0xFF03100F)],
          ),
        ),
        child: Stack(
          children: [
            const Positioned(
              top: -90,
              left: -80,
              child: _AmbientGlow(size: 240, color: AppTheme.primary),
            ),
            const Positioned(
              bottom: -110,
              right: -60,
              child: _AmbientGlow(size: 220, color: AppTheme.secondary),
            ),
            SafeArea(
              child: Center(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.all(20),
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 430),
                    child: Card(
                      child: Padding(
                        padding: const EdgeInsets.all(24),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const _BrandHeader(),
                            const SizedBox(height: 28),
                            Text(
                              'Inicia sesión',
                              style: theme.textTheme.headlineSmall?.copyWith(
                                fontSize: 30,
                              ),
                            ),
                            const SizedBox(height: 12),
                            Text(
                              'Accede a WiFiScope para registrar mediciones, revisar la red conectada y trabajar sobre tus planos.',
                              style: theme.textTheme.bodyMedium?.copyWith(
                                height: 1.5,
                              ),
                            ),
                            const SizedBox(height: 24),
                            _QuickAccessBanner(
                              emailController: _emailController,
                              passwordController: _passwordController,
                            ),
                            const SizedBox(height: 24),
                            Form(
                              key: _formKey,
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  _InputLabel(label: 'Correo electrónico'),
                                  const SizedBox(height: 8),
                                  TextFormField(
                                    controller: _emailController,
                                    keyboardType: TextInputType.emailAddress,
                                    textInputAction: TextInputAction.next,
                                    decoration: _inputDecoration(
                                      context,
                                      hintText: 'correo@ejemplo.com',
                                      prefixIcon: Icons.alternate_email,
                                    ),
                                    validator: (value) {
                                      final email = value?.trim() ?? '';
                                      if (email.isEmpty) {
                                        return 'Introduce tu correo electrónico.';
                                      }
                                      final emailRegex = RegExp(
                                        r'^[^@\s]+@[^@\s]+\.[^@\s]+$',
                                      );
                                      if (!emailRegex.hasMatch(email)) {
                                        return 'Introduce un correo válido.';
                                      }
                                      return null;
                                    },
                                  ),
                                  const SizedBox(height: 18),
                                  _InputLabel(label: 'Contraseña'),
                                  const SizedBox(height: 8),
                                  TextFormField(
                                    controller: _passwordController,
                                    obscureText: _obscurePassword,
                                    textInputAction: TextInputAction.done,
                                    onFieldSubmitted: (_) => _submit(),
                                    decoration: _inputDecoration(
                                      context,
                                      hintText: 'Mínimo 6 caracteres',
                                      prefixIcon: Icons.lock_outline,
                                      suffixIcon: IconButton(
                                        onPressed: () {
                                          setState(() {
                                            _obscurePassword =
                                                !_obscurePassword;
                                          });
                                        },
                                        icon: Icon(
                                          _obscurePassword
                                              ? Icons.visibility_outlined
                                              : Icons.visibility_off_outlined,
                                        ),
                                      ),
                                    ),
                                    validator: (value) {
                                      final password = value ?? '';
                                      if (password.isEmpty) {
                                        return 'Introduce tu contraseña.';
                                      }
                                      if (password.length < 6) {
                                        return 'La contraseña debe tener al menos 6 caracteres.';
                                      }
                                      return null;
                                    },
                                  ),
                                  const SizedBox(height: 18),
                                  Wrap(
                                    spacing: 12,
                                    runSpacing: 8,
                                    crossAxisAlignment:
                                        WrapCrossAlignment.center,
                                    children: [
                                      InkWell(
                                        borderRadius: BorderRadius.circular(14),
                                        onTap: () {
                                          setState(() {
                                            _rememberSession =
                                                !_rememberSession;
                                          });
                                        },
                                        child: Padding(
                                          padding: const EdgeInsets.symmetric(
                                            vertical: 4,
                                          ),
                                          child: Row(
                                            mainAxisSize: MainAxisSize.min,
                                            children: [
                                              Checkbox(
                                                value: _rememberSession,
                                                onChanged: (value) {
                                                  setState(() {
                                                    _rememberSession =
                                                        value ?? false;
                                                  });
                                                },
                                              ),
                                              Text(
                                                'Recordar sesión',
                                                style:
                                                    theme.textTheme.bodyMedium,
                                              ),
                                            ],
                                          ),
                                        ),
                                      ),
                                      TextButton(
                                        onPressed: () {
                                          ScaffoldMessenger.of(
                                            context,
                                          ).showSnackBar(
                                            const SnackBar(
                                              content: Text(
                                                'La recuperación de contraseña se conectará al backend en una siguiente etapa.',
                                              ),
                                            ),
                                          );
                                        },
                                        child: const Text(
                                          '¿Olvidaste tu contraseña?',
                                        ),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 10),
                                  SizedBox(
                                    width: double.infinity,
                                    child: FilledButton.icon(
                                      onPressed: _isSubmitting ? null : _submit,
                                      icon: _isSubmitting
                                          ? const SizedBox(
                                              width: 18,
                                              height: 18,
                                              child: CircularProgressIndicator(
                                                strokeWidth: 2,
                                              ),
                                            )
                                          : const Icon(Icons.login_rounded),
                                      label: Text(
                                        _isSubmitting
                                            ? 'Validando acceso...'
                                            : 'Entrar a WiFiScope',
                                      ),
                                    ),
                                  ),
                                  const SizedBox(height: 18),
                                  Text(
                                    'En esta fase el login funciona de forma local para probar la experiencia completa antes de conectarlo al backend.',
                                    style: theme.textTheme.bodySmall?.copyWith(
                                      height: 1.45,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

InputDecoration _inputDecoration(
  BuildContext context, {
  required String hintText,
  required IconData prefixIcon,
  Widget? suffixIcon,
}) {
  return InputDecoration(
    hintText: hintText,
    prefixIcon: Icon(prefixIcon),
    suffixIcon: suffixIcon,
    filled: true,
    fillColor: AppTheme.surfaceElevated.withAlpha(190),
    border: OutlineInputBorder(
      borderRadius: BorderRadius.circular(18),
      borderSide: BorderSide(color: AppTheme.primary.withAlpha(30)),
    ),
    enabledBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(18),
      borderSide: BorderSide(color: AppTheme.primary.withAlpha(28)),
    ),
    focusedBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(18),
      borderSide: const BorderSide(color: AppTheme.primary, width: 1.4),
    ),
    errorBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(18),
      borderSide: const BorderSide(color: Color(0xFFFF7A7A)),
    ),
    focusedErrorBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(18),
      borderSide: const BorderSide(color: Color(0xFFFF7A7A), width: 1.4),
    ),
  );
}

class _BrandHeader extends StatelessWidget {
  const _BrandHeader();

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Row(
      children: [
        Container(
          width: 72,
          height: 72,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(22),
            border: Border.all(color: AppTheme.primary.withAlpha(48)),
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [Color(0xFF0E2723), Color(0xFF081817)],
            ),
            boxShadow: [
              BoxShadow(
                color: AppTheme.primary.withAlpha(30),
                blurRadius: 24,
                offset: const Offset(0, 10),
              ),
            ],
          ),
          padding: const EdgeInsets.all(10),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(16),
            child: Image.asset(
              'assets/icons/wifiscope-app-icon.png',
              fit: BoxFit.cover,
            ),
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                AppConfig.appName,
                style: theme.textTheme.headlineSmall?.copyWith(fontSize: 28),
              ),
              const SizedBox(height: 6),
              Text(
                'Explora, mide y registra la cobertura WiFi de cada ambiente.',
                style: theme.textTheme.bodyMedium?.copyWith(height: 1.4),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _QuickAccessBanner extends StatelessWidget {
  const _QuickAccessBanner({
    required this.emailController,
    required this.passwordController,
  });

  final TextEditingController emailController;
  final TextEditingController passwordController;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surfaceElevated.withAlpha(220),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppTheme.secondary.withAlpha(46)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Acceso de prueba',
            style: theme.textTheme.titleSmall?.copyWith(
              color: AppTheme.secondary,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Puedes usar cualquier correo válido y una contraseña de al menos 6 caracteres para probar el login local.',
            style: theme.textTheme.bodySmall?.copyWith(height: 1.45),
          ),
          const SizedBox(height: 10),
          TextButton.icon(
            onPressed: () {
              emailController.text = 'demo@wifiscope.app';
              passwordController.text = 'wifi123';
            },
            icon: const Icon(Icons.auto_fix_high),
            label: const Text('Autocompletar acceso demo'),
          ),
        ],
      ),
    );
  }
}

class _InputLabel extends StatelessWidget {
  const _InputLabel({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Text(
      label,
      style: Theme.of(
        context,
      ).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w700),
    );
  }
}

class _AmbientGlow extends StatelessWidget {
  const _AmbientGlow({required this.size, required this.color});

  final double size;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          gradient: RadialGradient(
            colors: [color.withAlpha(45), color.withAlpha(0)],
          ),
        ),
      ),
    );
  }
}

class LoginResult {
  const LoginResult({required this.email, required this.rememberSession});

  final String email;
  final bool rememberSession;
}
