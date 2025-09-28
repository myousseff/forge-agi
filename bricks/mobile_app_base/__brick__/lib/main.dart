import 'package:flutter/material.dart';
import 'app_router.dart';
import 'chat_screen.dart';

void main() {
  runApp(ForgeApp());
}

class ForgeApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final theme = ThemeData(
      colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF{{primary_color.trimLeft('#')}})),
      useMaterial3: true,
    );
    return MaterialApp.router(
      title: '{{app_name}}',
      theme: theme,
      routerConfig: buildRouter(),
    );
  }
}
