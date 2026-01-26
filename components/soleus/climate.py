import esphome.codegen as cg
from esphome.components import climate_ir
import esphome.config_validation as cv

AUTO_LOAD = ["climate_ir"]

CONF_SUPPORTS_HEAT = "supports_heat"

soleus_ns = cg.esphome_ns.namespace("soleus")
SoleusClimate = soleus_ns.class_("SoleusClimate", climate_ir.ClimateIR)

CONFIG_SCHEMA = climate_ir.climate_ir_with_receiver_schema(SoleusClimate).extend({
    cv.Optional(CONF_SUPPORTS_HEAT, default=False): cv.boolean,
})

async def to_code(config):
    var = await climate_ir.new_climate_ir(config)
    cg.add(var.set_supports_heat(config[CONF_SUPPORTS_HEAT]))
