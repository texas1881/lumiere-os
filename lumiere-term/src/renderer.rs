// ╔══════════════════════════════════════════════════════════════╗
// ║          ✦ Lumière Terminal — GPU Renderer                   ║
// ╚══════════════════════════════════════════════════════════════╝
//!
//! wgpu tabanlı GPU-hızlandırmalı metin rendering.

use crate::config::Config;
use crate::terminal::Terminal;
use log::info;
use wgpu::util::DeviceExt;
use winit::window::Window;

/// GPU vertex.
#[repr(C)]
#[derive(Copy, Clone, Debug, bytemuck::Pod, bytemuck::Zeroable)]
struct Vertex {
    position: [f32; 2],
    color: [f32; 4],
    uv: [f32; 2],
}

/// GPU renderer.
pub struct Renderer {
    surface: wgpu::Surface<'static>,
    device: wgpu::Device,
    queue: wgpu::Queue,
    config: wgpu::SurfaceConfiguration,
    render_pipeline: wgpu::RenderPipeline,
    vertex_buffer: wgpu::Buffer,

    // Metin
    cell_width: f32,
    cell_height: f32,
    padding: f32,
    bg_color: [f32; 4],
    width: u32,
    height: u32,
}

impl Renderer {
    pub async fn new(window: &Window, app_config: &Config) -> Self {
        let size = window.inner_size();

        // wgpu instance
        let instance = wgpu::Instance::new(wgpu::InstanceDescriptor {
            backends: wgpu::Backends::all(),
            ..Default::default()
        });

        let surface = instance.create_surface(window).unwrap();

        // Adapter
        let adapter = instance
            .request_adapter(&wgpu::RequestAdapterOptions {
                power_preference: wgpu::PowerPreference::LowPower,
                compatible_surface: Some(&surface),
                force_fallback_adapter: false,
            })
            .await
            .expect("GPU adapter bulunamadı");

        info!("GPU: {}", adapter.get_info().name);

        // Device + Queue
        let (device, queue) = adapter
            .request_device(
                &wgpu::DeviceDescriptor {
                    label: Some("lumiere-term"),
                    required_features: wgpu::Features::empty(),
                    required_limits: wgpu::Limits::default(),
                    ..Default::default()
                },
                None,
            )
            .await
            .expect("GPU device alınamadı");

        // Surface config
        let surface_caps = surface.get_capabilities(&adapter);
        let surface_format = surface_caps
            .formats
            .iter()
            .find(|f| f.is_srgb())
            .copied()
            .unwrap_or(surface_caps.formats[0]);

        let config = wgpu::SurfaceConfiguration {
            usage: wgpu::TextureUsages::RENDER_ATTACHMENT,
            format: surface_format,
            width: size.width,
            height: size.height,
            present_mode: wgpu::PresentMode::Fifo,
            alpha_mode: surface_caps.alpha_modes[0],
            view_formats: vec![],
            desired_maximum_frame_latency: 2,
        };
        surface.configure(&device, &config);

        // Shader
        let shader = device.create_shader_module(wgpu::ShaderModuleDescriptor {
            label: Some("text_shader"),
            source: wgpu::ShaderSource::Wgsl(include_str!("shaders/text.wgsl").into()),
        });

        // Pipeline layout
        let pipeline_layout = device.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor {
            label: Some("pipeline_layout"),
            bind_group_layouts: &[],
            push_constant_ranges: &[],
        });

        // Render pipeline
        let render_pipeline = device.create_render_pipeline(&wgpu::RenderPipelineDescriptor {
            label: Some("render_pipeline"),
            layout: Some(&pipeline_layout),
            vertex: wgpu::VertexState {
                module: &shader,
                entry_point: Some("vs_main"),
                buffers: &[wgpu::VertexBufferLayout {
                    array_stride: std::mem::size_of::<Vertex>() as wgpu::BufferAddress,
                    step_mode: wgpu::VertexStepMode::Vertex,
                    attributes: &[
                        wgpu::VertexAttribute {
                            offset: 0,
                            shader_location: 0,
                            format: wgpu::VertexFormat::Float32x2,
                        },
                        wgpu::VertexAttribute {
                            offset: 8,
                            shader_location: 1,
                            format: wgpu::VertexFormat::Float32x4,
                        },
                        wgpu::VertexAttribute {
                            offset: 24,
                            shader_location: 2,
                            format: wgpu::VertexFormat::Float32x2,
                        },
                    ],
                }],
                compilation_options: Default::default(),
            },
            fragment: Some(wgpu::FragmentState {
                module: &shader,
                entry_point: Some("fs_main"),
                targets: &[Some(wgpu::ColorTargetState {
                    format: config.format,
                    blend: Some(wgpu::BlendState::ALPHA_BLENDING),
                    write_mask: wgpu::ColorWrites::ALL,
                })],
                compilation_options: Default::default(),
            }),
            primitive: wgpu::PrimitiveState {
                topology: wgpu::PrimitiveTopology::TriangleList,
                ..Default::default()
            },
            depth_stencil: None,
            multisample: wgpu::MultisampleState::default(),
            multiview: None,
            cache: None,
        });

        // Geçici vertex buffer (render sırasında güncellenecek)
        let vertex_buffer = device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("vertex_buffer"),
            size: 1024 * 1024, // 1MB
            usage: wgpu::BufferUsages::VERTEX | wgpu::BufferUsages::COPY_DST,
            mapped_at_creation: false,
        });

        // Hücre boyutlarını hesapla
        let cell_width = app_config.font_size * 0.6;
        let cell_height = app_config.font_size * 1.4;

        Self {
            surface,
            device,
            queue,
            config,
            render_pipeline,
            vertex_buffer,
            cell_width,
            cell_height,
            padding: app_config.padding as f32,
            bg_color: app_config.colors.background,
            width: size.width,
            height: size.height,
        }
    }

    /// Pencere boyutu değiştiğinde çağrılır.
    pub fn resize(&mut self, width: u32, height: u32) {
        if width > 0 && height > 0 {
            self.width = width;
            self.height = height;
            self.config.width = width;
            self.config.height = height;
            self.surface.configure(&self.device, &self.config);
        }
    }

    /// Grid boyutlarını hesapla (cols, rows).
    pub fn grid_dimensions(&self) -> (u16, u16) {
        let cols = ((self.width as f32 - 2.0 * self.padding) / self.cell_width) as u16;
        let rows = ((self.height as f32 - 2.0 * self.padding) / self.cell_height) as u16;
        (cols.max(1), rows.max(1))
    }

    /// Terminal'i GPU ile render et.
    pub fn render(&mut self, term: &Terminal) {
        let output = match self.surface.get_current_texture() {
            Ok(tex) => tex,
            Err(_) => {
                self.surface.configure(&self.device, &self.config);
                return;
            }
        };

        let view = output.texture.create_view(&wgpu::TextureViewDescriptor::default());

        // Vertex'leri oluştur
        let mut vertices = Vec::new();
        self.build_cell_quads(term, &mut vertices);
        self.build_cursor_quad(term, &mut vertices);

        // Buffer güncelle
        if !vertices.is_empty() {
            self.queue.write_buffer(
                &self.vertex_buffer,
                0,
                bytemuck::cast_slice(&vertices),
            );
        }

        // Render pass
        let mut encoder = self.device.create_command_encoder(
            &wgpu::CommandEncoderDescriptor { label: Some("encoder") },
        );

        {
            let mut render_pass = encoder.begin_render_pass(&wgpu::RenderPassDescriptor {
                label: Some("render_pass"),
                color_attachments: &[Some(wgpu::RenderPassColorAttachment {
                    view: &view,
                    resolve_target: None,
                    ops: wgpu::Operations {
                        load: wgpu::LoadOp::Clear(wgpu::Color {
                            r: self.bg_color[0] as f64,
                            g: self.bg_color[1] as f64,
                            b: self.bg_color[2] as f64,
                            a: self.bg_color[3] as f64,
                        }),
                        store: wgpu::StoreOp::Store,
                    },
                })],
                depth_stencil_attachment: None,
                ..Default::default()
            });

            if !vertices.is_empty() {
                render_pass.set_pipeline(&self.render_pipeline);
                render_pass.set_vertex_buffer(0, self.vertex_buffer.slice(..));
                render_pass.draw(0..vertices.len() as u32, 0..1);
            }
        }

        self.queue.submit(std::iter::once(encoder.finish()));
        output.present();
    }

    fn build_cell_quads(&self, term: &Terminal, vertices: &mut Vec<Vertex>) {
        let w = self.width as f32;
        let h = self.height as f32;

        for (row_idx, row) in term.grid.iter().enumerate() {
            for (col_idx, cell) in row.iter().enumerate() {
                // Arka plan (non-default)
                if cell.bg.r > 0.01 || cell.bg.g > 0.01 || cell.bg.b > 0.01 {
                    let x = self.padding + col_idx as f32 * self.cell_width;
                    let y = self.padding + row_idx as f32 * self.cell_height;
                    let color = [cell.bg.r, cell.bg.g, cell.bg.b, 1.0];
                    self.push_quad(vertices, x, y, self.cell_width, self.cell_height, color, w, h);
                }

                // Karakter (boşluk değilse)
                if cell.ch != ' ' {
                    let x = self.padding + col_idx as f32 * self.cell_width;
                    let y = self.padding + row_idx as f32 * self.cell_height;
                    let color = [cell.fg.r, cell.fg.g, cell.fg.b, 1.0];
                    // Basitleştirilmiş: her hücre için küçük bir quad
                    self.push_quad(
                        vertices,
                        x + self.cell_width * 0.15,
                        y + self.cell_height * 0.15,
                        self.cell_width * 0.7,
                        self.cell_height * 0.7,
                        color,
                        w,
                        h,
                    );
                }
            }
        }
    }

    fn build_cursor_quad(&self, term: &Terminal, vertices: &mut Vec<Vertex>) {
        if !term.cursor_visible { return; }

        let x = self.padding + term.cursor_x as f32 * self.cell_width;
        let y = self.padding + term.cursor_y as f32 * self.cell_height;
        let color = [0.961, 0.651, 0.137, 0.8]; // Lumière gold
        let w = self.width as f32;
        let h = self.height as f32;

        self.push_quad(vertices, x, y, self.cell_width, self.cell_height, color, w, h);
    }

    fn push_quad(&self, vertices: &mut Vec<Vertex>,
                 x: f32, y: f32, w: f32, h: f32,
                 color: [f32; 4], screen_w: f32, screen_h: f32) {
        // Piksel → NDC dönüşümü
        let ndc = |px: f32, py: f32| -> [f32; 2] {
            [
                (px / screen_w) * 2.0 - 1.0,
                1.0 - (py / screen_h) * 2.0,
            ]
        };

        let tl = ndc(x, y);
        let tr = ndc(x + w, y);
        let bl = ndc(x, y + h);
        let br = ndc(x + w, y + h);

        let uv_tl = [0.0, 0.0];
        let uv_tr = [1.0, 0.0];
        let uv_bl = [0.0, 1.0];
        let uv_br = [1.0, 1.0];

        // İki üçgen
        vertices.push(Vertex { position: tl, color, uv: uv_tl });
        vertices.push(Vertex { position: tr, color, uv: uv_tr });
        vertices.push(Vertex { position: bl, color, uv: uv_bl });

        vertices.push(Vertex { position: tr, color, uv: uv_tr });
        vertices.push(Vertex { position: br, color, uv: uv_br });
        vertices.push(Vertex { position: bl, color, uv: uv_bl });
    }
}
