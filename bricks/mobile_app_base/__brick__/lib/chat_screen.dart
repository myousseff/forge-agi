import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

const BASE_URL = 'http://10.0.2.2:8080';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});
  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  String? conversationId;
  final List<Map<String, dynamic>> messages = [];
  final TextEditingController controller = TextEditingController();
  bool loading = false;

  @override
  void initState() {
    super.initState();
    _initConversation();
  }

  Future<void> _initConversation() async {
    final resp = await http.post(Uri.parse('$BASE_URL/v1/agents'));
    if (resp.statusCode == 200) {
      setState(() {
        conversationId = json.decode(resp.body)['id'];
      });
    }
  }

  Future<void> _sendMessage(String text) async {
    if (conversationId == null) return;
    setState(() => loading = true);
    final msg = {'role': 'user', 'content': text};
    final resp = await http.post(
      Uri.parse('$BASE_URL/v1/chat'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'conversation_id': conversationId, 'message': msg}),
    );
    if (resp.statusCode == 200) {
      final data = json.decode(resp.body);
      setState(() {
        messages.addAll(List<Map<String, dynamic>>.from(data['messages']));
      });
    }
    setState(() => loading = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Chat')),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              itemCount: messages.length,
              itemBuilder: (context, idx) {
                final msg = messages[idx];
                if (msg['role'] == 'tool') {
                  final result = msg['content'];
                  // On attend une liste [{name, address, rating}] dans le message tool
                  try {
                    final items = json.decode(result) is List ? json.decode(result) : [];
                    return Card(
                      child: Column(
                        children: [
                          const Text('Résultats', style: TextStyle(fontWeight: FontWeight.bold)),
                          ...items.map<Widget>((item) => ListTile(
                                title: Text(item['name'] ?? ''),
                                subtitle: Text(item['address'] ?? ''),
                                trailing: Text('⭐ ${item['rating'] ?? ''}'),
                              )),
                        ],
                      ),
                    );
                  } catch (_) {
                    return Card(child: Text(result.toString()));
                  }
                }
                return ListTile(
                  title: Text(msg['role'] ?? ''),
                  subtitle: Text(msg['content'] ?? ''),
                );
              },
            ),
          ),
          if (loading) const LinearProgressIndicator(),
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: controller,
                    decoration: const InputDecoration(hintText: 'Message...'),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.send),
                  onPressed: loading
                      ? null
                      : () {
                          final text = controller.text.trim();
                          if (text.isNotEmpty) {
                            controller.clear();
                            _sendMessage(text);
                          }
                        },
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
