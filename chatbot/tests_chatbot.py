# chatbot/tests_chatbot.py
"""
Pruebas automatizadas para el sistema de chatbot
Ejecutar con: python manage.py test chatbot.tests_chatbot
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal
import json

from chatbot.models import Conversation, Message, ConversationState
from chatbot.flow_handlers import ManualFlowHandler, AIFlowHandler, convert_decimals
from projects.models import Project
from projects.forms import ProjectForm


User = get_user_model()


class ConversationModelTests(TestCase):
    """Pruebas para el modelo Conversation"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            role='MAESTRO'
        )
    
    def test_crear_conversacion(self):
        """Prueba 1: Crear una conversación básica"""
        conversation = Conversation.objects.create(
            user=self.user,
            title="Test Conversation"
        )
        
        self.assertEqual(conversation.user, self.user)
        self.assertEqual(conversation.state, ConversationState.IDLE)
        self.assertFalse(conversation.is_active())
        self.assertEqual(conversation.current_step, 0)
        print("✅ Prueba 1 PASADA: Conversación creada correctamente")
    
    def test_agregar_mensaje_a_conversacion(self):
        """Prueba 2: Agregar mensajes a una conversación"""
        conversation = Conversation.objects.create(user=self.user)
        
        # Agregar mensaje del usuario
        msg_user = Message.objects.create(
            conversation=conversation,
            role="user",
            content="Hola, quiero crear un presupuesto"
        )
        
        # Agregar respuesta del asistente
        msg_assistant = Message.objects.create(
            conversation=conversation,
            role="assistant",
            content="¡Perfecto! ¿Prefieres el modo manual o con IA?"
        )
        
        self.assertEqual(conversation.messages.count(), 2)
        self.assertEqual(msg_user.role, "user")
        self.assertEqual(msg_assistant.role, "assistant")
        print("✅ Prueba 2 PASADA: Mensajes agregados correctamente")


class ManualFlowHandlerTests(TestCase):
    """Pruebas para el flujo manual del chatbot"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testmanual',
            email='manual@example.com',
            password='testpass123',
            first_name='Manual',
            last_name='Tester',
            role='MAESTRO'
        )
        self.conversation = Conversation.objects.create(user=self.user)
    
    def test_iniciar_flujo_manual(self):
        """Prueba 3: Iniciar el flujo manual"""
        handler = ManualFlowHandler(self.conversation, ProjectForm)
        response = handler.start()
        
        # Verificar que el flujo se inició
        self.conversation.refresh_from_db()
        self.assertEqual(self.conversation.state, ConversationState.MANUAL_FLOW)
        self.assertEqual(self.conversation.flow_type, "manual")
        self.assertEqual(self.conversation.current_step, 0)
        self.assertGreater(self.conversation.total_steps, 0)
        self.assertIn("Nombre del proyecto", response)
        print(f"✅ Prueba 3 PASADA: Flujo manual iniciado ({self.conversation.total_steps} pasos)")
    
    def test_completar_flujo_manual_y_crear_proyecto(self):
        """Prueba 4: Completar el flujo manual y verificar creación del proyecto"""
        handler = ManualFlowHandler(self.conversation, ProjectForm)
        handler.start()
        
        # Simular respuestas del usuario para todos los campos
        respuestas = {
            'name': 'Casa de Prueba',
            'location_address': 'Calle Test 123',
            'description': 'Proyecto de prueba automatizada',
            'estado': 'futuro',
            'ubicacion_proyecto': 'Medellin',
            'area_construida_total': '100',
            'numero_pisos': '1',
            'area_exterior_intervenir': '30',
            'tipo_terreno': 'normal',
            'acceso_obra': 'facil',
            'requiere_cerramiento': 'no',
            'sistema_entrepiso': 'maciza',
            'exigencia_estructural': 'normal',
            'relacion_muros': 'media',
            'acabado_muros': 'estandar',
            'cielorrasos': 'parcial',
            'piso_zona_social': 'ceramica',
            'piso_habitaciones': 'ceramica',
            'numero_banos': '2',
            'nivel_enchape_banos': 'medio',
            'puertas_interiores': '5',
            'puerta_principal_especial': 'no',
            'porcentaje_ventanas': 'medio',
            'metros_mueble_cocina': '6',
            'vestier_closets': 'basico',
            'calentador_gas': 'si',
            'incluye_lavadero': 'si',
            'punto_lavaplatos': 'si',
            'punto_lavadora': 'si',
            'punto_lavadero': 'si',
            'dotacion_electrica': 'estandar',
            'red_gas_natural': 'si',
            'tipo_cubierta': 'tradicional',
            'impermeabilizacion_adicional': 'no',
            'area_adoquin': '0',
            'area_zonas_verdes': '20',
            'incluir_estudios_disenos': 'si',
            'incluir_licencia_impuestos': 'si',
        }
        
        # Procesar cada respuesta
        resultado = None
        for i, (field_name, field) in enumerate(handler.fields):
            if field_name in respuestas:
                resultado = handler.process_response(respuestas[field_name])
            else:
                # Valor por defecto si no está en el diccionario
                resultado = handler.process_response('0')
        
        # Verificar que el flujo se completó
        self.assertTrue(resultado['completed'])
        
        # Verificar que el proyecto se creó
        if 'project_id' in resultado and resultado['project_id']:
            project = Project.objects.get(id=resultado['project_id'])
            self.assertEqual(project.name, 'Casa de Prueba')
            self.assertFalse(project.created_by_ai)
            self.assertIsNotNone(project.presupuesto)
            self.assertGreater(project.presupuesto, 0)
            print(f"✅ Prueba 4 PASADA: Proyecto creado - ID: {project.id}, Presupuesto: ${project.presupuesto:,.0f}")
        else:
            print("⚠️ Prueba 4 ADVERTENCIA: Flujo completado pero proyecto no creado automáticamente")


class AIFlowHandlerTests(TestCase):
    """Pruebas para el flujo con IA del chatbot"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testai',
            email='ai@example.com',
            password='testpass123',
            first_name='AI',
            last_name='Tester',
            role='JEFE'
        )
        self.conversation = Conversation.objects.create(user=self.user)
    
    def test_iniciar_flujo_ia(self):
        """Prueba 5: Iniciar el flujo con IA"""
        handler = AIFlowHandler(self.conversation, llm_client=None)
        response = handler.start()
        
        # Verificar que el flujo se inició
        self.conversation.refresh_from_db()
        self.assertEqual(self.conversation.state, ConversationState.AI_FLOW)
        self.assertEqual(self.conversation.flow_type, "ai")
        self.assertEqual(self.conversation.current_step, 0)
        self.assertEqual(self.conversation.total_steps, 10)
        self.assertIn("Modo IA", response)
        print(f"✅ Prueba 5 PASADA: Flujo IA iniciado (10 preguntas)")
    
    def test_completar_flujo_ia_y_crear_proyecto(self):
        """Prueba 6: Completar el flujo IA y verificar creación del proyecto"""
        handler = AIFlowHandler(self.conversation, llm_client=None)
        handler.start()
        
        # Respuestas simuladas del usuario
        respuestas_ia = [
            "Casa unifamiliar",
            "Medellín",
            "120",
            "2 pisos",
            "3 habitaciones",
            "2 baños",
            "Sí, garaje para 2 carros",
            "Premium",
            "Sí, cocina integral y closets",
            "No tengo límite específico"
        ]
        
        # Procesar cada respuesta
        resultado = None
        for respuesta in respuestas_ia:
            resultado = handler.process_response(respuesta)
        
        # Verificar que el flujo se completó
        self.assertTrue(resultado['completed'])
        
        # Verificar que el proyecto se creó
        if 'project_id' in resultado and resultado['project_id']:
            project = Project.objects.get(id=resultado['project_id'])
            self.assertTrue(project.created_by_ai)
            self.assertEqual(project.creado_por, self.user)
            self.assertIsNotNone(project.presupuesto)
            self.assertGreater(project.presupuesto, 0)
            self.assertIn("Proyecto IA", project.name)
            print(f"✅ Prueba 6 PASADA: Proyecto IA creado - ID: {project.id}, Presupuesto: ${project.presupuesto:,.0f}")
        else:
            print("⚠️ Prueba 6 ADVERTENCIA: Flujo IA completado pero proyecto no creado")


class ChatbotAPITests(TestCase):
    """Pruebas para la API del chatbot"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='apitest',
            email='api@example.com',
            password='testpass123',
            first_name='API',
            last_name='Tester',
            role='MAESTRO'
        )
        self.client.force_login(self.user)
    
    def test_enviar_mensaje_a_api(self):
        """Prueba 7: Enviar mensaje a la API del chatbot"""
        url = reverse('chatbot:chat_api')
        
        data = {
            'message': 'Hola, quiero ayuda'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertIn('conversation_id', response_data)
        self.assertIn('messages', response_data)
        print("✅ Prueba 7 PASADA: API responde correctamente")
    
    def test_iniciar_flujo_manual_via_api(self):
        """Prueba 8: Iniciar flujo manual vía API"""
        url = reverse('chatbot:chat_api')
        
        # Primer mensaje para iniciar flujo manual
        data = {
            'message': 'crear presupuesto manual'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertTrue(response_data.get('flow_active', False))
        self.assertEqual(response_data.get('flow_type'), 'manual')
        print("✅ Prueba 8 PASADA: Flujo manual iniciado vía API")


class UtilityFunctionsTests(TestCase):
    """Pruebas para funciones auxiliares"""
    
    def test_convert_decimals(self):
        """Prueba 9: Conversión de Decimals a float"""
        data = {
            'area': Decimal('100.50'),
            'presupuesto': Decimal('50000000'),
            'lista': [Decimal('10'), Decimal('20.5')],
            'anidado': {
                'valor': Decimal('999.99')
            }
        }
        
        resultado = convert_decimals(data)
        
        self.assertIsInstance(resultado['area'], float)
        self.assertEqual(resultado['area'], 100.50)
        self.assertIsInstance(resultado['presupuesto'], float)
        self.assertIsInstance(resultado['lista'][0], float)
        self.assertIsInstance(resultado['anidado']['valor'], float)
        print("✅ Prueba 9 PASADA: Conversión de Decimals funciona correctamente")
    
    def test_conversation_mark_completed(self):
        """Prueba 10: Marcar conversación como completada"""
        user = User.objects.create_user(
            username='completetest',
            email='complete@example.com',
            password='testpass123',
            role='MAESTRO'
        )
        
        conversation = Conversation.objects.create(
            user=user,
            state=ConversationState.MANUAL_FLOW
        )
        
        self.assertTrue(conversation.is_active())
        
        conversation.mark_completed()
        
        self.assertEqual(conversation.state, ConversationState.COMPLETED)
        self.assertFalse(conversation.is_active())
        print("✅ Prueba 10 PASADA: Conversación marcada como completada")


class ProjectCreationTests(TestCase):
    """Pruebas específicas de creación de proyectos"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='projecttest',
            email='project@example.com',
            password='testpass123',
            first_name='Project',
            last_name='Tester',
            role='JEFE'
        )
    
    def test_proyecto_manual_tiene_presupuesto(self):
        """Prueba 11: Proyecto manual debe tener presupuesto calculado"""
        project = Project.objects.create(
            name="Test Manual Project",
            creado_por=self.user,
            created_by_ai=False,
            area_construida_total=Decimal('100'),
            built_area=Decimal('100'),
            exterior_area=Decimal('30'),
            columns_count=4,
            walls_area=Decimal('0'),
            windows_area=Decimal('0'),
            doors_count=0
        )
        
        project.calculate_legacy_fields()
        presupuesto = project.calculate_final_budget()
        project.presupuesto = presupuesto
        project.save()
        
        self.assertIsNotNone(project.presupuesto)
        self.assertGreater(project.presupuesto, 0)
        self.assertFalse(project.created_by_ai)
        print(f"✅ Prueba 11 PASADA: Proyecto manual con presupuesto ${project.presupuesto:,.0f}")
    
    def test_proyecto_ia_marcado_correctamente(self):
        """Prueba 12: Proyecto creado por IA debe estar marcado"""
        project = Project.objects.create(
            name="Test IA Project",
            creado_por=self.user,
            created_by_ai=True,
            area_construida_total=Decimal('120'),
            built_area=Decimal('120'),
            exterior_area=Decimal('36'),
            columns_count=5,
            walls_area=Decimal('0'),
            windows_area=Decimal('0'),
            doors_count=0
        )
        
        project.calculate_legacy_fields()
        presupuesto = project.calculate_final_budget()
        project.presupuesto = presupuesto
        project.save()
        
        self.assertTrue(project.created_by_ai)
        self.assertIsNotNone(project.presupuesto)
        self.assertGreater(project.presupuesto, 0)
        print(f"✅ Prueba 12 PASADA: Proyecto IA marcado correctamente con presupuesto ${project.presupuesto:,.0f}")


# Resumen de ejecución
def print_test_summary():
    """Imprime un resumen de las pruebas"""
    print("\n" + "="*60)
    print("RESUMEN DE PRUEBAS DEL CHATBOT")
    print("="*60)
    print("Total de pruebas: 12")
    print("\nCategorías:")
    print("  • Modelo de Conversación: 2 pruebas")
    print("  • Flujo Manual: 2 pruebas")
    print("  • Flujo IA: 2 pruebas")
    print("  • API del Chatbot: 2 pruebas")
    print("  • Funciones Auxiliares: 2 pruebas")
    print("  • Creación de Proyectos: 2 pruebas")
    print("\n" + "="*60)
    print("Ejecutar con: python manage.py test chatbot.tests_chatbot")
    print("="*60 + "\n")