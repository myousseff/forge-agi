import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'chat_screen.dart';

GoRouter buildRouter() {
  return GoRouter(
    initialLocation: '/chat',
    routes: [
      GoRoute(
        path: '/',
        builder: (context, state) => const HomeScreen(),
      ),
      GoRoute(
        path: '/chat',
        builder: (context, state) => const ChatScreen(),
      ),
      // TODO: routes supplémentaires auto-générées pour entities/screens
    ],
  );
}

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Home')),
      body: const Center(child: Text('App générée - Forge AGI')),
    );
  }
}
