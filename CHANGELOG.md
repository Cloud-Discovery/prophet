# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Docker Compose deployment support with separate frontend and backend containers
- Web interface with Vue.js and modern UI
- Application management with visual topology canvas
- RESTful API endpoints for all major features
- Sidebar resizing functionality in fullscreen canvas mode
- Preset color options for edge styling in canvas
- Containerized deployment with Redis, Celery, and Flask in backend container
- Bilingual documentation support (Chinese/English)
- Project structure documentation (PROJECT_STRUCTURE.md)
- Open source compliance files (CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md)
- GitHub issue and PR templates

### Changed

- Refactored project structure for better maintainability
- Updated documentation with comprehensive guides
- Improved deployment process with Docker Compose
- Enhanced edge styling logic in ApplicationCanvas and ApplicationDetail components
- Optimized application port configuration
- Updated package dependencies

### Fixed

- Various bug fixes and improvements
- Fixed VMware firmware boot type parsing bug
- Fixed host collection path creation issue

## [1.0.0] - 2021-10-20

### Added

- Initial release
- Network scanning functionality using nmap
- Host collection for Linux (via Ansible), Windows (via WMI), and VMware (via API)
- Report generation and analysis
- Docker image support
- CLI interface (`prophet-cli`) for scan, collect, and report operations
- Import host information file functionality
- Linux and Windows host analysis report
- VMware CBT (Changed Block Tracking) support display
- HA/DRS status in analysis report
- OpenStack API script
- Scan results CSV sample file in examples directory
- MAC address generation in collector
- Sensitive information removal in generated results
- Log file packaging
- SSH key authentication support
- Multiple virtualization platform support

### Changed

- Updated README.md for new prophet logo
- Refactored host report generation
- Moved network controller to scanner module
- Refactored VMware collector
- Refactored projects using driver pattern
- Optimized summary for collection
- Optimized argparse and logging initialization
- Updated to Python 3 in Dockerfile
- Separated collect and analysis logic
- Updated WMI version
- Updated pip mirror configuration to Tsinghua
- Updated tox.ini configuration
- Changed calculation to use float for parameter ava_ratio
- Optimized VMware VM collection and report display
- Improved Docker deployment process
- Set Chinese README as default

### Fixed

- Fixed docker tag issues
- Fixed docker build and push workflow
- Fixed bug when disk is VirtualDisk.RawDiskMappingVer1BackingInfo
- Fixed network device DistributedVirtualPortBackingInfo handling
- Fixed issue when vm.config is empty
- Fixed VMware host info output file suffix for VCenter and ESXi host
- Fixed unable to get MAC address and disk capacity of virtual machine
- Fixed PEP8 checking
- Fixed Dockerfile deployment issues
- Removed raise exception when scanning
- Fixed various VMware collection bugs and optimizations

### Removed

- Removed get name from summary
- Removed sensitive files and messages in generated results

[Unreleased]: https://github.com/Cloud-Discovery/prophet/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Cloud-Discovery/prophet/releases/tag/v1.0.0
