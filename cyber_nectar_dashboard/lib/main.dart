import 'package:flutter/material.dart';
import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:fl_chart/fl_chart.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';

void main() => runApp(const CyberNectarApp());

const Color bgColor = Color(0xFF011E31);
const Color primaryColor = Color(0xFFF69813);
const Color headerColor = Color(0xFFE8E8E8);

// CONFIGURATION - Change this for your environment
const String apiBaseUrl = 'https://zips-twitch-puppy.ngrok-free.dev';

class CyberNectarApp extends StatelessWidget {
  const CyberNectarApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Welcome',
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: bgColor,
        primaryColor: primaryColor,
        colorScheme: const ColorScheme.dark().copyWith(
          primary: primaryColor,
          secondary: headerColor,
          surface: bgColor,
        ),
        textTheme: const TextTheme(
          bodyLarge: TextStyle(fontFamily: 'Montserrat', color: Colors.white),
          bodyMedium: TextStyle(fontFamily: 'Montserrat', color: Colors.white),
          titleLarge: TextStyle(fontFamily: 'Montserrat', color: primaryColor),
        ),
      ),
      home: const LoginScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLoading = false;
  String _errorMessage = '';

  Future<void> _login() async {
    setState(() {
      _isLoading = true;
      _errorMessage = '';
    });

    try {
      final response = await http.post(
        Uri.parse('$apiBaseUrl/api/login'),
        headers: {
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true',
        },
        body: json.encode({
          'username': _usernameController.text,
          'password': _passwordController.text,
        }),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['success'] == true) {
          final apiKey = data['api_key'];
          if (mounted) {
            Navigator.pushReplacement(
              context,
              MaterialPageRoute(builder: (_) => MainDashboard(apiKey: apiKey)),
            );
          }
        } else {
          setState(() => _errorMessage = data['error'] ?? 'Login failed');
        }
      } else {
        setState(() => _errorMessage = 'Invalid credentials or server error');
      }
    } catch (e) {
      setState(() => _errorMessage = 'Connection error: $e');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          color: bgColor,
          image: DecorationImage(
            image: AssetImage('assets/background_cover.png'),
            fit: BoxFit.cover,
            colorFilter: ColorFilter.mode(Colors.black54, BlendMode.darken),
          ),
        ),
        child: Center(
          child: Container(
            width: 400,
            padding: const EdgeInsets.all(32),
            decoration: BoxDecoration(
              color: bgColor.withValues(alpha: 0.85),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: headerColor.withValues(alpha: 0.3)),
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Image.asset('assets/LOGO.png', height: 80),
                const SizedBox(height: 16),
                const Text('Welcome', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: primaryColor)),
                const SizedBox(height: 32),
                TextField(
                  controller: _usernameController,
                  style: const TextStyle(color: Colors.white),
                  decoration: InputDecoration(
                    labelText: 'Username',
                    labelStyle: const TextStyle(color: headerColor),
                    prefixIcon: const Icon(Icons.person, color: primaryColor),
                    enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: headerColor.withValues(alpha: 0.5))),
                    focusedBorder: const OutlineInputBorder(borderSide: BorderSide(color: primaryColor)),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _passwordController,
                  obscureText: true,
                  style: const TextStyle(color: Colors.white),
                  decoration: InputDecoration(
                    labelText: 'Password',
                    labelStyle: const TextStyle(color: headerColor),
                    prefixIcon: const Icon(Icons.lock, color: primaryColor),
                    enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: headerColor.withValues(alpha: 0.5))),
                    focusedBorder: const OutlineInputBorder(borderSide: BorderSide(color: primaryColor)),
                  ),
                ),
                const SizedBox(height: 24),
                if (_errorMessage.isNotEmpty) ...[
                  Text(_errorMessage, style: const TextStyle(color: Colors.redAccent)),
                  const SizedBox(height: 16),
                ],
                SizedBox(
                  width: double.infinity,
                  child: _isLoading 
                    ? const Center(child: CircularProgressIndicator(color: primaryColor))
                    : ElevatedButton(
                        onPressed: _login,
                        style: ElevatedButton.styleFrom(
                          padding: const EdgeInsets.all(16),
                          backgroundColor: primaryColor,
                          foregroundColor: bgColor,
                        ),
                        child: const Text('LOG IN', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                      ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class DashboardHeader extends StatelessWidget implements PreferredSizeWidget {
  final String currentRoute;
  final String apiKey;
  
  const DashboardHeader({super.key, required this.currentRoute, required this.apiKey});

  @override
  Size get preferredSize => const Size.fromHeight(80);

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: bgColor,
        border: Border(bottom: BorderSide(color: headerColor.withValues(alpha: 0.1), width: 1)),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              Image.asset('assets/TITLE.png', height: 250),
            ],
          ),
          Row(
            children: [
              TextButton(
                onPressed: () {
                  if (currentRoute != 'home') {
                    Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => MainDashboard(apiKey: apiKey)));
                  }
                },
                child: Text('Home', style: TextStyle(color: currentRoute == 'home' ? primaryColor : headerColor, fontSize: 16, fontWeight: FontWeight.bold)),
              ),
              const SizedBox(width: 16),
              TextButton(
                onPressed: () {
                  if (currentRoute != 'log') {
                    Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => AttackLogPage(apiKey: apiKey)));
                  }
                },
                child: Text('Log', style: TextStyle(color: currentRoute == 'log' ? primaryColor : headerColor, fontSize: 16, fontWeight: FontWeight.bold)),
              ),
              const SizedBox(width: 16),
              TextButton.icon(
                onPressed: () {
                  Navigator.pushAndRemoveUntil(context, MaterialPageRoute(builder: (_) => const LoginScreen()), (route) => false);
                },
                icon: const Icon(Icons.logout, color: Colors.grey, size: 18),
                label: const Text('Log Out', style: TextStyle(color: Colors.grey, fontSize: 16)),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class MainDashboard extends StatefulWidget {
  final String apiKey;
  const MainDashboard({super.key, required this.apiKey});

  @override
  State<MainDashboard> createState() => _MainDashboardState();
}

class _MainDashboardState extends State<MainDashboard> {
  int totalThreats = 0;
  double agentAccuracy = 0;
  double realF1Score = 0;
  double averageDelay = 0;
  String lastThreat = 'LOW';
  Map<String, int> threatDist = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0, 'CRITICAL': 0};
  Map<String, int> protocolDist = {};
  Map<String, double> delayByThreat = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0, 'CRITICAL': 0};
  Map<String, int> actionDist = {'BLOCK': 0, 'ISOLATE': 0, 'CHALLENGE': 0, 'ALLOW': 0};
  bool isLoading = true;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    fetchRealData();
    _timer = Timer.periodic(const Duration(seconds: 5), (timer) => fetchRealData());
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> fetchRealData() async {
    try {
      final response = await http.get(
        Uri.parse('$apiBaseUrl/api/metrics'),
        headers: {
          'X-API-Key': widget.apiKey,
          'ngrok-skip-browser-warning': 'true',
        },
      );
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          totalThreats = data['total_attacks'] ?? 0;
          agentAccuracy = (data['agent_accuracy'] ?? 0).toDouble();
          realF1Score = (data['f1_score'] ?? 0).toDouble();
          averageDelay = (data['avg_delay'] ?? 0).toDouble();
          lastThreat = data['last_threat_level'] ?? 'LOW';
          
          final dist = data['threat_distribution'] as Map<String, dynamic>? ?? {};
          threatDist = dist.map((key, value) => MapEntry(key, value as int));

          final pDist = data['protocol_distribution'] as Map<String, dynamic>? ?? {};
          protocolDist = pDist.map((key, value) => MapEntry(key, value as int));

          final dByT = data['delay_by_threat'] as Map<String, dynamic>? ?? {};
          delayByThreat = dByT.map((key, value) => MapEntry(key, (value as num).toDouble()));

          final aDist = data['action_distribution'] as Map<String, dynamic>? ?? {};
          actionDist = aDist.map((key, value) => MapEntry(key, value as int));
          
          isLoading = false;
        });
      }
    } catch (e) {
      debugPrint('Error fetching data: $e');
      setState(() => isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (isLoading){
    return Scaffold(
        appBar: DashboardHeader(currentRoute: 'home', apiKey: widget.apiKey),
        body: const Center(child: CircularProgressIndicator(color: primaryColor)),
      );
    }
    return Scaffold(
      appBar: DashboardHeader(currentRoute: 'home', apiKey: widget.apiKey),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            // Row 1: Total Threats & Accuracy/F1 Score
            Row(
              children: [
                Expanded(child: DashboardCard(
                  title: 'Total Threats Detected',
                  mainValue: '$totalThreats',
                  icon: Icons.shield,
                )),
                const SizedBox(width: 24),
                Expanded(child: DashboardCardSplit(
                  title: 'AI Agent Performance',
                  leftLabel: 'Overall Accuracy',
                  leftValue: '${agentAccuracy.toStringAsFixed(1)}%',
                  rightLabel: 'Real F1-Score',
                  rightValue: '${realF1Score.toStringAsFixed(1)}%', // Uses the exact mathematical F1-Score calculated by the honeypot backend
                )),
              ],
            ),
            const SizedBox(height: 24),

            // Row 2: Type of Threats & Response Time by Threat
            Row(
              children: [
                Expanded(child: ThreatChartCard(distribution: threatDist)),
                const SizedBox(width: 24),
                Expanded(child: ResponseTimeBarChart(delays: delayByThreat)),
              ],
            ),
            const SizedBox(height: 24),

            // Row 3: Action Breakdown & Protocols
            Row(
              children: [
                Expanded(child: ActionBreakdownCard(distribution: actionDist)),
                const SizedBox(width: 24),
                Expanded(child: ProtocolCard(protocols: protocolDist)),
              ],
            ),
            const SizedBox(height: 24),

            // Row 4: Physical Alert Status
            Row(
              children: [
                Expanded(child: PhysicalAlertCard(level: lastThreat)),
                const SizedBox(width: 24),
                const Expanded(child: SizedBox()), // Placeholder for symmetry
              ],
            ),
          ],
        ),
      ),
    );
  }
}

// UI CARDS

class DashboardCard extends StatelessWidget {
  final String title;
  final String mainValue;
  final IconData icon;

  const DashboardCard({super.key, required this.title, required this.mainValue, required this.icon});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: headerColor.withValues(alpha: 0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(title, style: const TextStyle(color: headerColor, fontSize: 16)),
              Icon(icon, color: primaryColor),
            ],
          ),
          const SizedBox(height: 16),
          Text(mainValue, style: const TextStyle(color: primaryColor, fontSize: 40, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
}

class DashboardCardSplit extends StatelessWidget {
  final String title;
  final String leftLabel;
  final String leftValue;
  final String rightLabel;
  final String rightValue;

  const DashboardCardSplit({
    super.key, required this.title,
    required this.leftLabel, required this.leftValue,
    required this.rightLabel, required this.rightValue,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: headerColor.withValues(alpha: 0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(color: headerColor, fontSize: 16)),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    Text(leftValue, style: const TextStyle(color: primaryColor, fontSize: 32, fontWeight: FontWeight.bold)),
                    Text(leftLabel, style: const TextStyle(color: headerColor, fontSize: 12)),
                  ],
                ),
              ),
              Container(width: 1, height: 50, color: headerColor.withValues(alpha: 0.5)),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    Text(rightValue, style: const TextStyle(color: primaryColor, fontSize: 32, fontWeight: FontWeight.bold)),
                    Text(rightLabel, style: const TextStyle(color: headerColor, fontSize: 12)),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class ThreatChartCard extends StatelessWidget {
  final Map<String, int> distribution;
  const ThreatChartCard({super.key, required this.distribution});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 300,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: headerColor.withValues(alpha: 0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Type of Threats', style: TextStyle(color: headerColor, fontSize: 16)),
          const SizedBox(height: 24),
          Expanded(
            child: PieChart(
              PieChartData(
                sectionsSpace: 2,
                centerSpaceRadius: 40,
                pieTouchData: PieTouchData(
                  touchCallback: (FlTouchEvent event, pieTouchResponse) {},
                  enabled: true,
                ),
                sections: [
                  PieChartSectionData(
                    value: (distribution['CRITICAL'] ?? 0).toDouble(), 
                    title: '${distribution['CRITICAL'] ?? 0}', 
                    color: const Color(0xFFD32F2F), 
                    radius: 50, 
                    titleStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                  PieChartSectionData(
                    value: (distribution['HIGH'] ?? 0).toDouble(), 
                    title: '${distribution['HIGH'] ?? 0}', 
                    color: const Color(0xFFF57C00), 
                    radius: 50, 
                    titleStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                  PieChartSectionData(
                    value: (distribution['MEDIUM'] ?? 0).toDouble(), 
                    title: '${distribution['MEDIUM'] ?? 0}', 
                    color: primaryColor, 
                    radius: 50, 
                    titleStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                  PieChartSectionData(
                    value: (distribution['LOW'] ?? 0).toDouble(), 
                    title: '${distribution['LOW'] ?? 0}', 
                    color: const Color(0xFF388E3C), 
                    radius: 50, 
                    titleStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _legendItem('Crit', const Color(0xFFD32F2F)),
              const SizedBox(width: 8),
              _legendItem('High', const Color(0xFFF57C00)),
              const SizedBox(width: 8),
              _legendItem('Med', primaryColor),
              const SizedBox(width: 8),
              _legendItem('Low', const Color(0xFF388E3C)),
            ],
          )
        ],
      ),
    );
  }

  Widget _legendItem(String label, Color color) {
    return Row(
      children: [
        Container(width: 10, height: 10, color: color),
        const SizedBox(width: 4),
        Text(label, style: const TextStyle(color: headerColor, fontSize: 10)),
      ],
    );
  }
}

class ResponseTimeBarChart extends StatelessWidget {
  final Map<String, double> delays;
  const ResponseTimeBarChart({super.key, required this.delays});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 300,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: headerColor.withValues(alpha: 0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Response Time by Threats', style: TextStyle(color: headerColor, fontSize: 16)),
          const SizedBox(height: 24),
          Expanded(
            child: BarChart(
              BarChartData(
                alignment: BarChartAlignment.spaceAround,
                maxY: 10,
                barTouchData: BarTouchData(enabled: true),
                titlesData: FlTitlesData(
                  show: true,
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      getTitlesWidget: (value, meta) {
                        const style = TextStyle(color: headerColor, fontSize: 10);
                        switch (value.toInt()) {
                          case 0: return const Text('Low', style: style);
                          case 1: return const Text('Med', style: style);
                          case 2: return const Text('High', style: style);
                          case 3: return const Text('Crit', style: style);
                          default: return const Text('');
                        }
                      },
                    ),
                  ),
                  leftTitles: AxisTitles(sideTitles: SideTitles(showTitles: true, reservedSize: 30, getTitlesWidget: (val, meta) => Text('${val.toInt()}s', style: const TextStyle(color: headerColor, fontSize: 10)))),
                  topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                ),
                gridData: FlGridData(show: false),
                borderData: FlBorderData(show: false),
                barGroups: [
                  BarChartGroupData(x: 0, barRods: [BarChartRodData(toY: delays['LOW'] ?? 0, color: const Color(0xFF388E3C), width: 25, borderRadius: BorderRadius.circular(4))]),
                  BarChartGroupData(x: 1, barRods: [BarChartRodData(toY: delays['MEDIUM'] ?? 0, color: primaryColor, width: 25, borderRadius: BorderRadius.circular(4))]),
                  BarChartGroupData(x: 2, barRods: [BarChartRodData(toY: delays['HIGH'] ?? 0, color: const Color(0xFFF57C00), width: 25, borderRadius: BorderRadius.circular(4))]),
                  BarChartGroupData(x: 3, barRods: [BarChartRodData(toY: delays['CRITICAL'] ?? 0, color: const Color(0xFFD32F2F), width: 25, borderRadius: BorderRadius.circular(4))]),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class ActionBreakdownCard extends StatelessWidget {
  final Map<String, int> distribution;
  const ActionBreakdownCard({super.key, required this.distribution});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 250,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: headerColor.withValues(alpha: 0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('RL Action Status Breakdown', style: TextStyle(color: headerColor, fontSize: 16)),
          const SizedBox(height: 16),
          Expanded(
            child: PieChart(
              PieChartData(
                sectionsSpace: 2,
                centerSpaceRadius: 30,
                sections: [
                  PieChartSectionData(value: (distribution['ISOLATE'] ?? 0).toDouble(), title: 'ISO', color: Colors.redAccent, radius: 35, titleStyle: const TextStyle(fontSize: 10, color: Colors.white)),
                  PieChartSectionData(value: (distribution['BLOCK'] ?? 0).toDouble(), title: 'BLK', color: Colors.orangeAccent, radius: 35, titleStyle: const TextStyle(fontSize: 10, color: Colors.white)),
                  PieChartSectionData(value: (distribution['CHALLENGE'] ?? 0).toDouble(), title: 'CHA', color: Colors.yellowAccent, radius: 35, titleStyle: const TextStyle(fontSize: 10, color: Colors.black)),
                  PieChartSectionData(value: (distribution['ALLOW'] ?? 0).toDouble(), title: 'ALW', color: Colors.greenAccent, radius: 35, titleStyle: const TextStyle(fontSize: 10, color: Colors.black)),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class ProtocolCard extends StatelessWidget {
  final Map<String, int> protocols;
  const ProtocolCard({super.key, required this.protocols});

  @override
  Widget build(BuildContext context) {
    List<MapEntry<String, int>> sortedProtocols = protocols.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));
      
    return Container(
      height: 250,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: headerColor.withValues(alpha: 0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Honeypot Protocols', style: TextStyle(color: headerColor, fontSize: 16)),
          const SizedBox(height: 16),
          Expanded(
            child: sortedProtocols.isEmpty 
            ? const Center(child: Text("No protocols detected yet.", style: TextStyle(color: Colors.grey)))
            : ListView.builder(
              itemCount: sortedProtocols.length,
              itemBuilder: (context, index) {
                final protocol = sortedProtocols[index];
                return Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(protocol.key, style: const TextStyle(color: Colors.white, fontSize: 14)),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                        decoration: BoxDecoration(color: primaryColor.withValues(alpha: 0.2), borderRadius: BorderRadius.circular(12)),
                        child: Text('${protocol.value}', style: const TextStyle(color: primaryColor, fontWeight: FontWeight.bold)),
                      ),
                    ],
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class PhysicalAlertCard extends StatelessWidget {
  final String level;
  const PhysicalAlertCard({super.key, required this.level});

  @override
  Widget build(BuildContext context) {
    Color statColor = Colors.green;
    List<Color> gradientColors = [Colors.green.withValues(alpha: 0.1), bgColor];
    
    if (level == 'CRITICAL') {
      statColor = Colors.red;
      gradientColors = [Colors.red.withValues(alpha: 0.15), bgColor];
    } else if (level == 'HIGH') {
      statColor = Colors.orange;
      gradientColors = [Colors.orange.withValues(alpha: 0.15), bgColor];
    } else if (level == 'MEDIUM') {
      statColor = Colors.yellow;
      gradientColors = [Colors.yellow.withValues(alpha: 0.1), bgColor];
    }

    return Container(
      height: 250,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: headerColor.withValues(alpha: 0.2)),
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: gradientColors,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Text('Physical Alert Status', style: TextStyle(color: headerColor, fontSize: 16)),
          const SizedBox(height: 16), // Reduced from 24
          Icon(Icons.sensors, color: statColor, size: 60), // Reduced from 64
          const SizedBox(height: 12), // Reduced from 16
          Text(level, style: TextStyle(color: statColor, fontSize: 32, fontWeight: FontWeight.bold)),
          const SizedBox(height: 4), // Reduced from 8
          const Text('ESP32 Integration Active', style: TextStyle(color: headerColor, fontSize: 13)), // Reduced from 14
        ],
      ),
    );
  }
}

// LOG PAGE

class AttackLogPage extends StatefulWidget {
  final String apiKey;
  const AttackLogPage({super.key, required this.apiKey});

  @override
  State<AttackLogPage> createState() => _AttackLogPageState();
}

class _AttackLogPageState extends State<AttackLogPage> {
  List<dynamic> attacks = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    fetchAttacks();
  }

  Future<void> fetchAttacks() async {
    try {
      final response = await http.get(
        Uri.parse('$apiBaseUrl/api/live_attacks'),
        headers: {
          'X-API-Key': widget.apiKey,
          'ngrok-skip-browser-warning': 'true',
        },
      );
      if (response.statusCode == 200) {
        setState(() {
          attacks = json.decode(response.body);
          isLoading = false;
        });
      }
    } catch (e) {
      debugPrint('Error: $e');
      setState(() => isLoading = false);
    }
  }

  Future<void> _generatePdfReport() async {
    final pdf = pw.Document();
    
    // fetch latest metrics for the summary section
    final metricsResponse = await http.get(
      Uri.parse('https://zips-twitch-puppy.ngrok-free.dev/api/metrics'),
      headers: {
        'X-API-Key': widget.apiKey,
        'ngrok-skip-browser-warning': 'true',
      },
    );
    final metrics = metricsResponse.statusCode == 200 ? json.decode(metricsResponse.body) : {};
    
    final logoImage = await imageFromAssetBundle('assets/LOGO.png');
    
    pdf.addPage(
      pw.Page(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.all(32),
        build: (pw.Context context) {
          return pw.Column(
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              // Header with logo
              pw.Row(
                mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
                children: [
                  pw.Column(
                    crossAxisAlignment: pw.CrossAxisAlignment.start,
                    children: [
                      pw.Text('Incident Report', style: pw.TextStyle(fontSize: 40, fontWeight: pw.FontWeight.bold, color: PdfColor.fromHex('#f69813'))),
                      pw.SizedBox(height: 8),
                      pw.Text('Generated: ${DateTime.now().toString().substring(0, 19)}', style: const pw.TextStyle(fontSize: 10, color: PdfColors.grey600)),
                    ],
                  ),
                  pw.Image(logoImage, height: 60),
                ],
              ),
              pw.SizedBox(height: 32),
              
              // Summary Section
              pw.Text('Summary', style: pw.TextStyle(fontSize: 18, fontWeight: pw.FontWeight.bold)),
              pw.Divider(thickness: 1, color: PdfColors.grey300),
              pw.SizedBox(height: 12),
              pw.Row(
                mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
                children: [
                  pw.Column(
                    crossAxisAlignment: pw.CrossAxisAlignment.start,
                    children: [
                      _pdfSummaryItem('Total Threats:', '${metrics['total_attacks'] ?? 0}'),
                      _pdfSummaryItem('Agent Accuracy:', '${(metrics['agent_accuracy'] ?? 0).toStringAsFixed(1)}%'),
                    ],
                  ),
                  pw.Column(
                    crossAxisAlignment: pw.CrossAxisAlignment.start,
                    children: [
                      _pdfSummaryItem('Real F1-Score:', '${(metrics['f1_score'] ?? 0).toStringAsFixed(1)}%'),
                      _pdfSummaryItem('Last Threat:', '${metrics['last_threat_level'] ?? 'N/A'}'),
                    ],
                  ),
                ],
              ),
              pw.SizedBox(height: 32),
              
              // Threats Distribution Section
              pw.Column(
                crossAxisAlignment: pw.CrossAxisAlignment.start,
                children: [
                  pw.Text('Threats Distribution', style: pw.TextStyle(fontSize: 18, fontWeight: pw.FontWeight.bold)),
                  pw.Divider(thickness: 1, color: PdfColors.grey300),
                  pw.SizedBox(height: 20),
                  
                  pw.Center(
                    child: pw.Text('Frequency Overview', style: pw.TextStyle(fontStyle: pw.FontStyle.italic, color: PdfColors.grey600)),
                  ),
                  pw.SizedBox(height: 12),
                  
                  // Enlarged Table
                  pw.Table(
                    border: pw.TableBorder.all(color: PdfColors.black, width: 0.8),
                    children: [
                      _pdfTableHeader(['Severity Level', 'Total Attacks']),
                      _pdfTableRow(['Critical', '${metrics['threat_distribution']?['CRITICAL'] ?? 0}']),
                      _pdfTableRow(['High', '${metrics['threat_distribution']?['HIGH'] ?? 0}']),
                      _pdfTableRow(['Medium', '${metrics['threat_distribution']?['MEDIUM'] ?? 0}']),
                      _pdfTableRow(['Low', '${metrics['threat_distribution']?['LOW'] ?? 0}']),
                    ],
                  ),
                  
                  pw.SizedBox(height: 40),
                  
                  // Visual Breakdown at the bottom
                  pw.Center(
                    child: pw.Column(
                      children: [
                        pw.Text('Visual Breakdown', style: pw.TextStyle(fontSize: 14, fontWeight: pw.FontWeight.bold, color: PdfColors.grey700)),
                        pw.SizedBox(height: 16),
                        pw.SizedBox(
                          height: 200, // Increased height for better visibility
                          width: 250,
                          child: pw.Chart(
                            grid: pw.PieGrid(),
                            datasets: [
                              pw.PieDataSet(
                                legend: 'Crit',
                                value: (metrics['threat_distribution']?['CRITICAL'] ?? 0).toDouble(),
                                color: PdfColor.fromHex('#D32F2F'),
                              ),
                              pw.PieDataSet(
                                legend: 'High',
                                value: (metrics['threat_distribution']?['HIGH'] ?? 0).toDouble(),
                                color: PdfColor.fromHex('#F57C00'),
                              ),
                              pw.PieDataSet(
                                legend: 'Med',
                                value: (metrics['threat_distribution']?['MEDIUM'] ?? 0).toDouble(),
                                color: PdfColor.fromHex('#F69813'),
                              ),
                              pw.PieDataSet(
                                legend: 'Low',
                                value: (metrics['threat_distribution']?['LOW'] ?? 0).toDouble(),
                                color: PdfColor.fromHex('#388E3C'),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              
              pw.Spacer(),
              pw.Divider(thickness: 0.5, color: PdfColors.grey400),
              pw.Center(child: pw.Text('Cyber Nectar - Automated IoT Defense System', style: const pw.TextStyle(fontSize: 8, color: PdfColors.grey500))),
            ],
          );
        },
      ),
    );

    await Printing.layoutPdf(
      onLayout: (PdfPageFormat format) async => pdf.save(),
      name: 'Cyber_Nectar_Incident_Report.pdf',
    );
  }

  pw.Widget _pdfSummaryItem(String label, String value) {
    return pw.Padding(
      padding: const pw.EdgeInsets.symmetric(vertical: 4),
      child: pw.Row(
        children: [
          pw.Text(label, style: pw.TextStyle(fontWeight: pw.FontWeight.bold, fontSize: 12)),
          pw.SizedBox(width: 8),
          pw.Text(value, style: const pw.TextStyle(fontSize: 12)),
        ],
      ),
    );
  }

  pw.TableRow _pdfTableHeader(List<String> items) {
    return pw.TableRow(
      decoration: const pw.BoxDecoration(color: PdfColors.grey100),
      children: items.map((i) => pw.Container(
        padding: const pw.EdgeInsets.all(8),
        alignment: pw.Alignment.center,
        child: pw.Text(i, style: pw.TextStyle(fontWeight: pw.FontWeight.bold)),
      )).toList(),
    );
  }

  pw.TableRow _pdfTableRow(List<String> items) {
    return pw.TableRow(
      children: items.map((i) => pw.Container(
        padding: const pw.EdgeInsets.all(8),
        alignment: pw.Alignment.center,
        child: pw.Text(i),
      )).toList(),
    );
  }

  Color _getActionColor(String action) {
    if (action == 'ISOLATE' || action == 'CRITICAL') return Colors.red;
    if (action == 'BLOCK' || action == 'HIGH') return Colors.orange;
    if (action == 'CHALLENGE' || action == 'MEDIUM') return Colors.yellow;
    return Colors.green;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: DashboardHeader(currentRoute: 'log', apiKey: widget.apiKey),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(24),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Live Attack Logs', style: TextStyle(color: primaryColor, fontSize: 24, fontWeight: FontWeight.bold)),
                Row(
                  children: [
                    ElevatedButton.icon(
                      onPressed: fetchAttacks,
                      icon: const Icon(Icons.refresh),
                      label: const Text('Refresh'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: bgColor,
                        foregroundColor: headerColor,
                        side: BorderSide(color: headerColor.withValues(alpha: 0.3)),
                      ),
                    ),
                    const SizedBox(width: 16),
                    ElevatedButton.icon(
                      onPressed: _generatePdfReport,
                      icon: const Icon(Icons.picture_as_pdf),
                      label: const Text('Export PDF'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: primaryColor,
                        foregroundColor: bgColor,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          Expanded(
            child: isLoading 
              ? const Center(child: CircularProgressIndicator(color: primaryColor))
              : Container(
                  margin: const EdgeInsets.symmetric(horizontal: 24),
                  decoration: BoxDecoration(
                    color: bgColor,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: headerColor.withValues(alpha: 0.2)),
                  ),
                  child: Column(
                    children: [
                      // Table Header
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                        decoration: BoxDecoration(
                          color: headerColor.withValues(alpha: 0.05),
                          border: Border(bottom: BorderSide(color: headerColor.withValues(alpha: 0.2))),
                        ),
                        child: Row(
                          children: const [
                            Expanded(flex: 2, child: Text('Timestamp', style: TextStyle(color: headerColor, fontWeight: FontWeight.bold))),
                            Expanded(flex: 2, child: Text('IP Address', style: TextStyle(color: headerColor, fontWeight: FontWeight.bold))),
                            Expanded(flex: 3, child: Text('Attack Protocol', style: TextStyle(color: headerColor, fontWeight: FontWeight.bold))),
                            Expanded(flex: 2, child: Text('Action', style: TextStyle(color: headerColor, fontWeight: FontWeight.bold))),
                          ],
                        ),
                      ),
                      // Table Body
                      Expanded(
                        child: ListView.builder(
                          itemCount: attacks.length,
                          itemBuilder: (context, index) {
                            final attack = attacks[attacks.length - 1 - index]; // latest first
                            final String timestamp = attack['timestamp']?.substring(11, 19) ?? 'N/A';
                            final String ip = attack['attack_data']?['source_ip'] ?? 'unknown';
                            final String protocol = attack['attack_type'] ?? 'Unknown Protocol';
                            final String action = attack['rl_action'] ?? 'ALLOW';

                            return Container(
                              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                              decoration: BoxDecoration(
                                border: Border(bottom: BorderSide(color: headerColor.withValues(alpha: 0.1))),
                              ),
                              child: Row(
                                children: [
                                  Expanded(flex: 2, child: Text(timestamp, style: const TextStyle(color: Colors.white70))),
                                  Expanded(flex: 2, child: Text(ip, style: const TextStyle(color: Colors.white))),
                                  Expanded(flex: 3, child: Text(protocol, style: const TextStyle(color: primaryColor, fontWeight: FontWeight.w500))),
                                  Expanded(
                                    flex: 2, 
                                    child: Align(
                                      alignment: Alignment.centerLeft,
                                      child: Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                                        decoration: BoxDecoration(
                                          color: _getActionColor(action).withValues(alpha: 0.1),
                                          borderRadius: BorderRadius.circular(12),
                                          border: Border.all(color: _getActionColor(action).withValues(alpha: 0.5)),
                                        ),
                                        child: Text(action, style: TextStyle(color: _getActionColor(action), fontSize: 12, fontWeight: FontWeight.bold)),
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            );
                          },
                        ),
                      ),
                    ],
                  ),
                ),
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }
}
