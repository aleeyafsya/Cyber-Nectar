import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:cyber_honeycomb_dashboard/main.dart'; 

void main() {
  group('Functionality Testing - Unit & Widget Tests', () {
    
    testWidgets('FT-UT-01: Verify Login Screen UI Components Render correctly', (WidgetTester tester) async {
  
      await tester.pumpWidget(const CyberNectarApp());

      // Vverify welcome text and fields are rendered
      expect(find.text('Welcome'), findsWidgets);
      
      // look for the text fields 
      expect(find.byType(TextField), findsNWidgets(2)); 
      
      // ;ook for the login button
      expect(find.text('LOG IN'), findsOneWidget);
    });

    testWidgets('FT-UT-02: Verify Username and Password inputs accept text', (WidgetTester tester) async {
      await tester.pumpWidget(const CyberNectarApp());

      final usernameField = find.byType(TextField).first;
      final passwordField = find.byType(TextField).last;

      await tester.enterText(usernameField, 'admin');
      await tester.enterText(passwordField, 'fyp26');

      // verify the text was entered successfully into the fields
      expect(find.text('admin'), findsOneWidget);
      expect(find.text('fyp26'), findsOneWidget);
    });

    testWidgets('FT-UT-03: Verify Dashboard Header navigation buttons exist', (WidgetTester tester) async {
      // Build the header component directly to test its isolated functionality
      await tester.pumpWidget(const MaterialApp(
        home: Scaffold(
          appBar: DashboardHeader(currentRoute: 'home', apiKey: 'test_key'),
        ),
      ));

      // check if Home, Log, and Log Out buttons exist
      expect(find.text('Home'), findsOneWidget);
      expect(find.text('Log'), findsOneWidget);
      expect(find.text('Log Out'), findsOneWidget);
    });
  });
}
