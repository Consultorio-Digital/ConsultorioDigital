import json
from pathlib import Path

from django.core.management.base import BaseCommand

from consultorio.models import Consultorio


DATA_PATH = Path(__file__).resolve().parents[3] / "utils" / "data" / "geodata.json"


class Command(BaseCommand):
    help = "Reemplaza los datos sintéticos de consultorios con datos reales del MINSAL."

    def handle(self, *args, **options):
        self.stdout.write("Eliminando datos sintéticos...")
        Consultorio.objects.all().delete()

        self.stdout.write(f"Leyendo {DATA_PATH}...")
        data = json.loads(DATA_PATH.read_text(encoding="utf-8"))

        consultorios = []
        for entry in data:
            f = entry["fields"]
            consultorios.append(Consultorio(
                objectid  = f["objectid"],
                nombre    = f["nombre"],
                c_reg     = f["c_reg"],
                nom_reg   = f["nom_reg"],
                c_com     = f["c_com"],
                nom_com   = f["nom_com"],
                c_ant     = f["c_ant"],
                c_vig     = f["c_vig"],
                c_mad     = f["c_mad"],
                c_nmad    = f["c_nmad"],
                c_depend  = f["c_depend"],
                depen     = f["depen"],
                perenec   = f["perenec"],
                tipo      = f["tipo"],
                ambito    = f["ambito"],
                urgencia  = f["urgencia"],
                certifica = f["certifica"],
                depen_a   = f["depen_a"],
                nivel     = f["nivel"],
                via       = f["via"],
                numero    = f["numero"],
                direccion = f["direccion"],
                fono      = f.get("fono"),
                f_inicio  = f["f_inicio"],
                f_reaper  = f["f_reaper"],
                sapu      = f["sapu"],
                f_cambio  = f["f_cambio"],
                tipo_camb = f["tipo_camb"],
                prestador = f["prestador"],
                estado    = f["estado"],
                nivel_com = f["nivel_com"],
                modalidad = f["modalidad"],
                latitud   = f["latitud"],
                longitud  = f["longitud"],
            ))

        Consultorio.objects.bulk_create(consultorios)
        self.stdout.write(self.style.SUCCESS(
            f"✓ {len(consultorios)} consultorios reales cargados ({len({c.nom_reg for c in consultorios})} regiones)."
        ))
