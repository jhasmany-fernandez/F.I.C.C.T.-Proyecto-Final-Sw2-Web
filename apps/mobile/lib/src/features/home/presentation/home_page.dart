import 'dart:io';
import 'dart:async';

import 'package:ficct_final_app/src/core/config/app_config.dart';
import 'package:ficct_final_app/src/core/theme/app_theme.dart';
import 'package:ficct_final_app/src/data/models/measurement_record.dart';
import 'package:ficct_final_app/src/data/models/project_snapshot.dart';
import 'package:ficct_final_app/src/data/models/wifi_reading.dart';
import 'package:ficct_final_app/src/data/repositories/local_measurement_repository.dart';
import 'package:ficct_final_app/src/features/floor_plan/application/floor_plan_service.dart';
import 'package:ficct_final_app/src/features/wifi_scan/application/wifi_connection_service.dart';
import 'package:ficct_final_app/src/features/wifi_scan/application/wifi_scan_service.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

class HomePage extends StatefulWidget {
  const HomePage({this.currentUserEmail, this.onLogout, super.key});

  final String? currentUserEmail;
  final VoidCallback? onLogout;

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  static const double _canvasWidth = 1000;

  final LocalMeasurementRepository _repository = LocalMeasurementRepository();
  final FloorPlanService _floorPlanService = FloorPlanService();
  final WifiConnectionService _wifiConnectionService = WifiConnectionService();
  final WifiScanService _wifiScanService = WifiScanService();

  ProjectSnapshot _snapshot = ProjectSnapshot.empty();
  Offset? _selectedPoint;
  bool _isBusy = true;
  bool _isScanning = false;
  String? _connectedWifiName;
  String? _connectedWifiBssid;
  int? _currentWifiRssi;
  final List<int> _wifiSignalHistory = [];
  String? _statusMessage;
  Timer? _wifiSignalTimer;

  @override
  void initState() {
    super.initState();
    _loadSnapshot();
  }

  Future<void> _loadSnapshot() async {
    ProjectSnapshot snapshot;

    try {
      snapshot = await _repository.loadSnapshot();
    } catch (_) {
      snapshot = ProjectSnapshot.empty();
    }

    if (!mounted) {
      return;
    }

    setState(() {
      _snapshot = snapshot;
      _isBusy = false;
    });

    await _loadConnectedWifiName();
    _startWifiSignalMonitoring();
  }

  @override
  void dispose() {
    _wifiSignalTimer?.cancel();
    super.dispose();
  }

  Future<void> _pickFloorPlan() async {
    setState(() {
      _statusMessage = null;
    });

    final floorPlan = await _floorPlanService.pickFloorPlan();
    if (floorPlan == null || !mounted) {
      return;
    }

    final updated = await _repository.replaceSnapshot(
      ProjectSnapshot(floorPlan: floorPlan, measurements: const []),
    );

    if (!mounted) {
      return;
    }

    setState(() {
      _snapshot = updated;
      _selectedPoint = null;
      _statusMessage =
          'Plano cargado correctamente. Ahora toca el lugar donde quieres registrar la señal WiFi.';
    });

    await _loadConnectedWifiName();
  }

  Future<void> _captureMeasurement() async {
    final floorPlan = _snapshot.floorPlan;
    final selectedPoint = _selectedPoint;

    if (floorPlan == null || selectedPoint == null) {
      return;
    }

    setState(() {
      _isScanning = true;
      _statusMessage = 'Midiendo la señal WiFi en la ubicación seleccionada...';
    });

    final scanResult = await _wifiScanService.scan();
    if (!mounted) {
      return;
    }

    if (!scanResult.isSuccess) {
      setState(() {
        _isScanning = false;
        _statusMessage = scanResult.errorMessage;
      });
      return;
    }

    final measurement = MeasurementRecord(
      id: 'measurement-${DateTime.now().millisecondsSinceEpoch}',
      floorPlanId: floorPlan.id,
      x: selectedPoint.dx,
      y: selectedPoint.dy,
      createdAt: DateTime.now(),
      readings: scanResult.readings,
    );

    final updatedSnapshot = await _repository.addMeasurement(measurement);

    if (!mounted) {
      return;
    }

    setState(() {
      _snapshot = updatedSnapshot;
      _isScanning = false;
      _selectedPoint = null;
      _statusMessage =
          'Medición guardada correctamente. Se detectaron ${scanResult.readings.length} redes WiFi.';
    });

    await _loadConnectedWifiName();
  }

  Future<void> _loadConnectedWifiName() async {
    final wifiInfo = await _wifiConnectionService.getConnectedWifiInfo();

    if (!mounted) {
      return;
    }

    setState(() {
      _connectedWifiName = wifiInfo?.ssid;
      _connectedWifiBssid = wifiInfo?.bssid;
    });

    await _refreshConnectedWifiSignal();
  }

  Future<void> _refreshConnectedWifiSignal() async {
    final wifiName = _connectedWifiName;
    if (wifiName == null || wifiName.isEmpty) {
      return;
    }

    final reading = await _wifiScanService.scanCurrentNetwork(
      ssid: wifiName,
      bssid: _connectedWifiBssid,
    );

    if (!mounted || reading == null) {
      return;
    }

    setState(() {
      _currentWifiRssi = reading.rssi;
      _wifiSignalHistory.add(reading.rssi);
      if (_wifiSignalHistory.length > 12) {
        _wifiSignalHistory.removeAt(0);
      }
    });
  }

  void _startWifiSignalMonitoring() {
    _wifiSignalTimer?.cancel();
    _wifiSignalTimer = Timer.periodic(const Duration(seconds: 3), (_) {
      _refreshConnectedWifiSignal();
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    if (_isBusy) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text(AppConfig.appName),
        actions: [
          if (widget.currentUserEmail != null)
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: Center(
                child: Text(
                  widget.currentUserEmail!,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: AppTheme.textMuted,
                  ),
                ),
              ),
            ),
          TextButton.icon(
            onPressed: _pickFloorPlan,
            icon: const Icon(Icons.upload_file_outlined),
            label: const Text('Cargar plano'),
          ),
          if (widget.onLogout != null)
            IconButton(
              onPressed: widget.onLogout,
              tooltip: 'Cerrar sesión',
              icon: const Icon(Icons.logout_rounded),
            ),
          const SizedBox(width: 12),
        ],
      ),
      body: DecoratedBox(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFF071412), Color(0xFF06100F), Color(0xFF0B1D19)],
          ),
        ),
        child: Stack(
          children: [
            const Positioned(
              top: -80,
              left: -60,
              child: _AmbientGlow(size: 220, color: AppTheme.primary),
            ),
            const Positioned(
              right: -70,
              top: 160,
              child: _AmbientGlow(size: 180, color: AppTheme.secondary),
            ),
            SafeArea(
              child: LayoutBuilder(
                builder: (context, constraints) {
                  final wideLayout = constraints.maxWidth >= 1100;
                  final horizontalPadding = wideLayout ? 24.0 : 16.0;
                  final verticalPadding = wideLayout ? 24.0 : 16.0;

                  if (wideLayout) {
                    return Padding(
                      padding: EdgeInsets.symmetric(
                        horizontal: horizontalPadding,
                        vertical: verticalPadding,
                      ),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Expanded(
                            flex: 3,
                            child: _buildWorkspace(theme, isCompact: false),
                          ),
                          const SizedBox(width: 24),
                          Expanded(
                            flex: 2,
                            child: _buildControlPanel(theme, isCompact: false),
                          ),
                        ],
                      ),
                    );
                  }

                  return ListView(
                    padding: EdgeInsets.symmetric(
                      horizontal: horizontalPadding,
                      vertical: verticalPadding,
                    ),
                    children: [
                      _buildWorkspace(theme, isCompact: true),
                      const SizedBox(height: 16),
                      _buildControlPanel(theme, isCompact: true),
                    ],
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildWorkspace(ThemeData theme, {required bool isCompact}) {
    final floorPlan = _snapshot.floorPlan;
    final selectedPoint = _selectedPoint;

    if (floorPlan == null) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(28),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Registrar mediciones WiFi',
                style: theme.textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 16),
              Text(
                'Sube el plano del ambiente que quieres analizar. Luego toca el '
                'lugar donde estás ubicado para registrar la señal WiFi en ese punto.',
                style: theme.textTheme.bodyLarge?.copyWith(height: 1.5),
              ),
              const SizedBox(height: 24),
              FilledButton.icon(
                onPressed: _pickFloorPlan,
                icon: const Icon(Icons.map_outlined),
                label: const Text('Cargar plano del ambiente'),
              ),
              const SizedBox(height: 24),
              _InfoBanner(
                title: 'Antes de comenzar',
                message:
                    'La medición real de redes WiFi funciona en Android. Asegúrate de tener el WiFi y la ubicación del teléfono activados.',
              ),
            ],
          ),
        ),
      );
    }

    final canvasHeight = _canvasWidth * (floorPlan.height / floorPlan.width);
    final selectedCoordinates = selectedPoint == null
        ? 'Todavía no has elegido una ubicación. Toca una zona del plano para continuar.'
        : 'Ubicación seleccionada correctamente. Ya puedes medir la señal WiFi en este punto.';

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Plano del ambiente',
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              floorPlan.name,
              style: theme.textTheme.bodySmall?.copyWith(
                color: AppTheme.textMuted.withAlpha(180),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Marca en el plano el lugar exacto donde estás parado para guardar la medición en esa ubicación.',
              style: theme.textTheme.bodyMedium?.copyWith(
                color: AppTheme.textMuted,
              ),
            ),
            const SizedBox(height: 16),
            _WifiNetworkBanner(
              wifiName: _connectedWifiName,
              currentRssi: _currentWifiRssi,
              signalHistory: _wifiSignalHistory,
            ),
            const SizedBox(height: 16),
            Wrap(
              spacing: 10,
              runSpacing: 10,
              children: const [
                _HintChip(
                  icon: Icons.touch_app_outlined,
                  label: 'Toca el lugar a medir',
                ),
                _HintChip(
                  icon: Icons.zoom_in_outlined,
                  label: 'Usa dos dedos para acercar',
                ),
                _HintChip(
                  icon: Icons.pan_tool_alt_outlined,
                  label: 'Arrastra para moverte',
                ),
              ],
            ),
            const SizedBox(height: 16),
            _InfoBanner(
              title: 'Ubicación actual',
              message: selectedCoordinates,
            ),
            const SizedBox(height: 20),
            if (isCompact)
              SizedBox(
                height: 360,
                child: _buildPlanViewer(
                  floorPlanImagePath: floorPlan.imagePath,
                  canvasHeight: canvasHeight,
                  selectedPoint: selectedPoint,
                ),
              )
            else
              Expanded(
                child: _buildPlanViewer(
                  floorPlanImagePath: floorPlan.imagePath,
                  canvasHeight: canvasHeight,
                  selectedPoint: selectedPoint,
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildPlanViewer({
    required String floorPlanImagePath,
    required double canvasHeight,
    required Offset? selectedPoint,
  }) {
    return DecoratedBox(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: AppTheme.primary.withAlpha(55)),
        gradient: const LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [Color(0xFF0D201C), Color(0xFF081614)],
        ),
        boxShadow: [
          BoxShadow(
            color: AppTheme.primary.withAlpha(24),
            blurRadius: 28,
            offset: const Offset(0, 12),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: LayoutBuilder(
          builder: (context, constraints) {
            final scale = _fitScale(
              sourceWidth: _canvasWidth,
              sourceHeight: canvasHeight,
              maxWidth: constraints.maxWidth,
              maxHeight: constraints.maxHeight,
            );
            final fittedWidth = _canvasWidth * scale;
            final fittedHeight = canvasHeight * scale;

            return ClipRRect(
              borderRadius: BorderRadius.circular(18),
              child: DecoratedBox(
                decoration: const BoxDecoration(color: Color(0xFF071110)),
                child: InteractiveViewer(
                  boundaryMargin: const EdgeInsets.all(32),
                  maxScale: 6,
                  minScale: 0.8,
                  child: Center(
                    child: GestureDetector(
                      onTapDown: (details) {
                        final localX = (details.localPosition.dx / scale).clamp(
                          0.0,
                          _canvasWidth,
                        );
                        final localY = (details.localPosition.dy / scale).clamp(
                          0.0,
                          canvasHeight,
                        );

                        final normalizedDx = (localX / _canvasWidth).clamp(
                          0.0,
                          1.0,
                        );
                        final normalizedDy = (localY / canvasHeight).clamp(
                          0.0,
                          1.0,
                        );

                        setState(() {
                          _selectedPoint = Offset(normalizedDx, normalizedDy);
                        });
                      },
                      child: SizedBox(
                        width: fittedWidth,
                        height: fittedHeight,
                        child: Stack(
                          children: [
                            Positioned.fill(
                              child: _PlanImage(imagePath: floorPlanImagePath),
                            ),
                            Positioned.fill(
                              child: IgnorePointer(
                                child: CustomPaint(painter: _PlanGridPainter()),
                              ),
                            ),
                            ..._snapshot.measurements.map(
                              (measurement) => _PointMarker(
                                position: Offset(
                                  measurement.x * fittedWidth,
                                  measurement.y * fittedHeight,
                                ),
                                color: AppTheme.primary,
                                label: '${measurement.readings.length} redes',
                                selected: false,
                              ),
                            ),
                            if (selectedPoint != null)
                              _PointMarker(
                                position: Offset(
                                  selectedPoint.dx * fittedWidth,
                                  selectedPoint.dy * fittedHeight,
                                ),
                                color: AppTheme.secondary,
                                label: 'Punto seleccionado',
                                selected: true,
                              ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }

  Widget _buildControlPanel(ThemeData theme, {required bool isCompact}) {
    final floorPlan = _snapshot.floorPlan;
    final selectedPoint = _selectedPoint;
    final measurements = _snapshot.measurements;

    final summaryCard = Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Resumen de la medición',
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 16),
            _KeyValueRow(
              label: 'Plano cargado',
              value: floorPlan?.name ?? 'Aún no cargado',
            ),
            const SizedBox(height: 12),
            _KeyValueRow(label: 'Mediciones', value: '${measurements.length}'),
            const SizedBox(height: 12),
            _KeyValueRow(
              label: 'Ubicación actual',
              value: selectedPoint == null
                  ? 'No seleccionada'
                  : 'Lista para medir señal en este punto',
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed:
                    floorPlan == null || selectedPoint == null || _isScanning
                    ? null
                    : _captureMeasurement,
                icon: _isScanning
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.wifi_find),
                label: Text(
                  _isScanning
                      ? 'Midiendo señal WiFi...'
                      : 'Medir señal WiFi aquí',
                ),
              ),
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: _pickFloorPlan,
                icon: const Icon(Icons.image_outlined),
                label: Text(
                  measurements.isEmpty
                      ? 'Elegir otro plano'
                      : 'Cambiar plano y empezar de nuevo',
                ),
              ),
            ),
            if (_statusMessage != null) ...[
              const SizedBox(height: 16),
              _InfoBanner(title: 'Mensaje', message: _statusMessage!),
            ],
          ],
        ),
      ),
    );

    final measurementsCard = Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Historial de mediciones',
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 12),
            if (measurements.isEmpty)
              Text(
                'Todavía no has guardado mediciones. Selecciona una ubicación en el plano y presiona el botón para medir.',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: AppTheme.textMuted,
                ),
              )
            else if (isCompact)
              ListView.separated(
                itemCount: measurements.length,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                separatorBuilder: (context, index) => const Divider(height: 24),
                itemBuilder: (context, index) {
                  final measurement = measurements[index];
                  return _MeasurementTile(measurement: measurement);
                },
              )
            else
              SizedBox(
                height: 420,
                child: ListView.separated(
                  itemCount: measurements.length,
                  separatorBuilder: (context, index) =>
                      const Divider(height: 24),
                  itemBuilder: (context, index) {
                    final measurement = measurements[index];
                    return _MeasurementTile(measurement: measurement);
                  },
                ),
              ),
          ],
        ),
      ),
    );

    if (isCompact) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        mainAxisSize: MainAxisSize.min,
        children: [summaryCard, const SizedBox(height: 16), measurementsCard],
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [summaryCard, const SizedBox(height: 20), measurementsCard],
    );
  }
}

double _fitScale({
  required double sourceWidth,
  required double sourceHeight,
  required double maxWidth,
  required double maxHeight,
}) {
  if (sourceWidth <= 0 || sourceHeight <= 0) {
    return 1;
  }

  final widthScale = maxWidth / sourceWidth;
  final heightScale = maxHeight / sourceHeight;
  return widthScale < heightScale ? widthScale : heightScale;
}

class _PlanImage extends StatelessWidget {
  const _PlanImage({required this.imagePath});

  final String imagePath;

  @override
  Widget build(BuildContext context) {
    if (kIsWeb) {
      return ColoredBox(
        color: const Color(0xFF071110),
        child: Center(
          child: Text(
            'La carga local de planos está pensada para Android.',
            style: Theme.of(context).textTheme.bodyMedium,
          ),
        ),
      );
    }

    return Image.file(
      File(imagePath),
      fit: BoxFit.contain,
      errorBuilder: (context, error, stackTrace) {
        return ColoredBox(
          color: const Color(0xFF071110),
          child: Center(
            child: Text(
              'No se pudo mostrar el plano seleccionado.',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ),
        );
      },
    );
  }
}

class _PointMarker extends StatelessWidget {
  const _PointMarker({
    required this.position,
    required this.color,
    required this.label,
    required this.selected,
  });

  final Offset position;
  final Color color;
  final String label;
  final bool selected;

  @override
  Widget build(BuildContext context) {
    final markerSize = selected ? 24.0 : 18.0;

    return Positioned(
      left: position.dx - (markerSize / 2),
      top: position.dy - (markerSize / 2),
      child: Tooltip(
        message: label,
        child: Stack(
          alignment: Alignment.center,
          children: [
            if (selected)
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: color.withAlpha(46),
                ),
              ),
            Container(
              width: markerSize,
              height: markerSize,
              decoration: BoxDecoration(
                color: color,
                shape: BoxShape.circle,
                border: Border.all(color: Colors.white, width: 2),
                boxShadow: const [
                  BoxShadow(
                    color: Color(0x66000000),
                    blurRadius: 14,
                    offset: Offset(0, 4),
                  ),
                ],
              ),
            ),
            Container(
              width: 4,
              height: 4,
              decoration: const BoxDecoration(
                color: Colors.white,
                shape: BoxShape.circle,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _HintChip extends StatelessWidget {
  const _HintChip({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: AppTheme.surfaceElevated.withAlpha(210),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: AppTheme.primary.withAlpha(45)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: AppTheme.primary),
          const SizedBox(width: 8),
          Text(label),
        ],
      ),
    );
  }
}

class _WifiNetworkBanner extends StatelessWidget {
  const _WifiNetworkBanner({
    required this.wifiName,
    required this.currentRssi,
    required this.signalHistory,
  });

  final String? wifiName;
  final int? currentRssi;
  final List<int> signalHistory;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final hasWifi = wifiName != null && wifiName!.isNotEmpty;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: hasWifi
            ? AppTheme.surfaceElevated.withAlpha(220)
            : const Color(0xFF2A2110),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color: hasWifi
              ? AppTheme.primary.withAlpha(70)
              : const Color(0xFFD2A53A),
        ),
        boxShadow: [
          BoxShadow(
            color: (hasWifi ? AppTheme.primary : const Color(0xFFD2A53A))
                .withAlpha(20),
            blurRadius: 22,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(
                      hasWifi ? Icons.wifi : Icons.wifi_off,
                      color: hasWifi
                          ? AppTheme.primary
                          : const Color(0xFFF6C35E),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Red WiFi actual',
                            style: theme.textTheme.titleSmall?.copyWith(
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            hasWifi
                                ? wifiName!
                                : 'No fue posible identificar la red conectada.',
                            style: theme.textTheme.bodyMedium?.copyWith(
                              color: AppTheme.textMuted,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                _SignalHistoryChart(
                  values: signalHistory,
                  currentRssi: currentRssi,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SignalHistoryChart extends StatelessWidget {
  const _SignalHistoryChart({required this.values, required this.currentRssi});

  final List<int> values;
  final int? currentRssi;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final hasData = values.isNotEmpty;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xAA081110),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.primary.withAlpha(35)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Wrap(
            spacing: 12,
            runSpacing: 6,
            alignment: WrapAlignment.spaceBetween,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              Text(
                'Intensidad reciente de la señal',
                style: theme.textTheme.titleSmall,
              ),
              Text(
                currentRssi == null ? '-- dBm' : '$currentRssi dBm',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: AppTheme.primary,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          SizedBox(
            height: 72,
            child: hasData
                ? CustomPaint(
                    painter: _SignalChartPainter(values: values),
                    child: const SizedBox.expand(),
                  )
                : Center(
                    child: Text(
                      'Aún no hay suficientes muestras para el gráfico.',
                      style: theme.textTheme.bodySmall,
                    ),
                  ),
          ),
        ],
      ),
    );
  }
}

class _SignalChartPainter extends CustomPainter {
  const _SignalChartPainter({required this.values});

  final List<int> values;

  @override
  void paint(Canvas canvas, Size size) {
    final gridPaint = Paint()
      ..color = AppTheme.primary.withAlpha(20)
      ..strokeWidth = 1;

    for (int i = 1; i <= 3; i++) {
      final y = size.height * (i / 4);
      canvas.drawLine(Offset(0, y), Offset(size.width, y), gridPaint);
    }

    const minRssi = -100.0;
    const maxRssi = -30.0;

    if (values.length == 1) {
      final normalized = ((values.first - minRssi) / (maxRssi - minRssi)).clamp(
        0.0,
        1.0,
      );
      final y = size.height - (normalized * size.height);

      final glowPaint = Paint()..color = AppTheme.primary.withAlpha(40);
      canvas.drawCircle(Offset(size.width / 2, y), 18, glowPaint);
      canvas.drawCircle(
        Offset(size.width / 2, y),
        6,
        Paint()..color = AppTheme.primary,
      );
      return;
    }

    if (values.length < 2) {
      return;
    }
    final stepX = size.width / (values.length - 1);
    final points = <Offset>[];

    for (int index = 0; index < values.length; index++) {
      final normalized = ((values[index] - minRssi) / (maxRssi - minRssi))
          .clamp(0.0, 1.0);
      final x = index * stepX;
      final y = size.height - (normalized * size.height);
      points.add(Offset(x, y));
    }

    final areaPath = Path()..moveTo(points.first.dx, size.height);
    for (final point in points) {
      areaPath.lineTo(point.dx, point.dy);
    }
    areaPath
      ..lineTo(points.last.dx, size.height)
      ..close();

    final areaPaint = Paint()
      ..shader = LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: [AppTheme.primary.withAlpha(90), AppTheme.primary.withAlpha(8)],
      ).createShader(Offset.zero & size);
    canvas.drawPath(areaPath, areaPaint);

    final linePaint = Paint()
      ..shader = const LinearGradient(
        colors: [AppTheme.secondary, AppTheme.primary],
      ).createShader(Offset.zero & size)
      ..strokeWidth = 3
      ..style = PaintingStyle.stroke;

    final linePath = Path()..moveTo(points.first.dx, points.first.dy);
    for (int i = 1; i < points.length; i++) {
      final previous = points[i - 1];
      final current = points[i];
      final controlX = (previous.dx + current.dx) / 2;
      linePath.cubicTo(
        controlX,
        previous.dy,
        controlX,
        current.dy,
        current.dx,
        current.dy,
      );
    }
    canvas.drawPath(linePath, linePaint);

    final markerPaint = Paint()..color = AppTheme.primary;
    final lastPoint = points.last;
    canvas.drawCircle(lastPoint, 5, markerPaint);
    canvas.drawCircle(
      lastPoint,
      10,
      Paint()..color = AppTheme.primary.withAlpha(35),
    );
  }

  @override
  bool shouldRepaint(covariant _SignalChartPainter oldDelegate) {
    if (oldDelegate.values.length != values.length) {
      return true;
    }

    for (int i = 0; i < values.length; i++) {
      if (oldDelegate.values[i] != values[i]) {
        return true;
      }
    }

    return false;
  }
}

class _PlanGridPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = AppTheme.primary.withAlpha(24)
      ..strokeWidth = 1;

    const step = 80.0;

    for (double x = step; x < size.width; x += step) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), paint);
    }

    for (double y = step; y < size.height; y += step) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _MeasurementTile extends StatelessWidget {
  const _MeasurementTile({required this.measurement});

  final MeasurementRecord measurement;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final strongestSignal = measurement.readings.isEmpty
        ? null
        : measurement.readings.reduce(
            (current, next) => current.rssi >= next.rssi ? current : next,
          );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Ubicación ${(measurement.x * 100).toStringAsFixed(1)}%, '
          '${(measurement.y * 100).toStringAsFixed(1)}%',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w700,
          ),
        ),
        const SizedBox(height: 6),
        Text(
          'Se registraron ${measurement.readings.length} redes WiFi en este punto',
          style: theme.textTheme.bodyMedium?.copyWith(
            color: const Color(0xFF475569),
          ),
        ),
        if (strongestSignal != null) ...[
          const SizedBox(height: 10),
          _TopReadingCard(reading: strongestSignal),
        ],
      ],
    );
  }
}

class _TopReadingCard extends StatelessWidget {
  const _TopReadingCard({required this.reading});

  final WifiReading reading;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final ssid = reading.ssid.isEmpty ? 'SSID oculto' : reading.ssid;

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppTheme.surfaceElevated.withAlpha(220),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppTheme.primary.withAlpha(35)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            ssid,
            style: theme.textTheme.titleSmall?.copyWith(
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 8),
          Text('BSSID ${reading.bssid}', style: theme.textTheme.bodySmall),
          const SizedBox(height: 4),
          Text(
            'RSSI ${reading.rssi} dBm | ${reading.frequency} MHz'
            '${reading.channel == null ? '' : ' | Canal ${reading.channel}'}',
            style: theme.textTheme.bodySmall?.copyWith(
              color: AppTheme.textMuted,
            ),
          ),
        ],
      ),
    );
  }
}

class _InfoBanner extends StatelessWidget {
  const _InfoBanner({required this.title, required this.message});

  final String title;
  final String message;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surfaceElevated.withAlpha(225),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppTheme.primary.withAlpha(55)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: theme.textTheme.titleSmall?.copyWith(
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            message,
            style: theme.textTheme.bodyMedium?.copyWith(height: 1.45),
          ),
        ],
      ),
    );
  }
}

class _KeyValueRow extends StatelessWidget {
  const _KeyValueRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 130,
          child: Text(
            label,
            style: theme.textTheme.bodyMedium?.copyWith(
              fontWeight: FontWeight.w700,
              color: AppTheme.textPrimary,
            ),
          ),
        ),
        Expanded(
          child: Text(
            value,
            style: theme.textTheme.bodyMedium?.copyWith(
              color: AppTheme.textMuted,
            ),
          ),
        ),
      ],
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
