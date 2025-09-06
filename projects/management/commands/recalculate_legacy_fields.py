from django.core.management.base import BaseCommand
from projects.models import Project

class Command(BaseCommand):
    help = 'Recalcula campos heredados de todos los proyectos existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--project-id',
            type=int,
            help='ID específico del proyecto a recalcular (opcional)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar recálculo incluso si los campos ya tienen valores'
        )

    def handle(self, *args, **options):
        project_id = options.get('project_id')
        force = options.get('force')
        
        if project_id:
            # Recalcular proyecto específico
            try:
                project = Project.objects.get(id=project_id)
                self.recalculate_project(project, force)
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Proyecto "{project.name}" (ID: {project.id}) recalculado exitosamente')
                )
            except Project.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ Proyecto con ID {project_id} no encontrado')
                )
        else:
            # Recalcular todos los proyectos
            projects = Project.objects.all()
            total_projects = projects.count()
            
            if total_projects == 0:
                self.stdout.write(
                    self.style.WARNING('⚠️ No hay proyectos para recalcular')
                )
                return
            
            self.stdout.write(f'🔄 Recalculando {total_projects} proyectos...')
            
            updated_count = 0
            for project in projects:
                try:
                    self.recalculate_project(project, force)
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ {project.name} (ID: {project.id}) - OK')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ {project.name} (ID: {project.id}) - Error: {str(e)}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'\n🎉 Proceso completado: {updated_count}/{total_projects} proyectos actualizados')
            )

    def recalculate_project(self, project, force=False):
        """Recalcula campos heredados de un proyecto específico"""
        if not force:
            # Verificar si ya tiene valores calculados
            if (project.walls_area and project.walls_area > 0 and 
                project.windows_area and project.windows_area > 0 and 
                project.doors_count and project.doors_count > 0):
                return
        
        # Calcular campos heredados
        project.calculate_legacy_fields()
        
        # Calcular presupuesto actualizado
        project.presupuesto = project.calculate_detailed_budget()
        
        # Guardar cambios
        project.save()
