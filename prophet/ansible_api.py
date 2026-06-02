#!/usr/bin/env python
# -*- coding=utf8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2019 Prophet Tech (Shanghai) Ltd.
#
# Authors: Li ZengYuan <lizengyuan@prophetech.cn>
#
# Copyright (c) 2019 This file is confidential and proprietary.
# All Rights Resrved, Prophet Tech (Shanghai) Ltd (http://www.prophetech.cn).
#
# AnsibleApi Class get host info - Rewritten for Ansible 9.8.0
#
# Steps:
#
#     1. Definition Callback
#     2. Ansible objects
#     3. Run ansibles

import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import yaml
from collections import namedtuple
from typing import Dict, List, Optional, Any

# Ansible 9.x imports (ansible-core)
try:
    from ansible import constants as ansible_constants
    from ansible.executor.task_queue_manager import TaskQueueManager
    from ansible.inventory.manager import InventoryManager
    from ansible.parsing.dataloader import DataLoader
    from ansible.playbook.play import Play
    from ansible.plugins.callback import CallbackBase
    from ansible.vars.manager import VariableManager
    from ansible.module_utils.common.collections import ImmutableDict
    from ansible.config.manager import ConfigManager, ensure_type
    ANSIBLE_AVAILABLE = True
except ImportError as e:
    logging.error(f"Failed to import Ansible modules: {e}")
    logging.error("Please install ansible-core: pip install ansible-core")
    ANSIBLE_AVAILABLE = False
    # Create dummy classes to avoid import errors
TaskQueueManager = None
InventoryManager = None
DataLoader = None
Play = None
CallbackBase = None
VariableManager = None


# Create ResultCallback class conditionally
if CallbackBase is not None:
    _BaseClass = CallbackBase
else:
    _BaseClass = object

class ResultCallback(_BaseClass):
    """Result callback for Ansible 9.x - collects task execution results"""
    
    def __init__(self, *args, **kwargs):
        """Initialize callback with result storage"""
        if CallbackBase is not None:
            try:
                super().__init__(*args, **kwargs)
            except Exception:
                # If parent init fails, just continue
                pass
        self.host_ok = {}
        self.host_failed = {}
        self.host_unreachable = {}
        self.host_skipped = {}
        self._playbook_start_called = False
        self._task_start_called = False
    
    def v2_runner_on_ok(self, result, *args, **kwargs):
        """Called when a task succeeds"""
        logging.info("v2_runner_on_ok called!")
        try:
            host_name = self._get_host_name(result)
            logging.info(f"v2_runner_on_ok: host_name={host_name}, result type={type(result)}")
            self.host_ok[host_name] = result
            logging.info(f"host_ok now has {len(self.host_ok)} entries: {list(self.host_ok.keys())}")
            
            # Also store by IP if available
            if hasattr(result, '_result') and isinstance(result._result, dict):
                ansible_facts = result._result.get('ansible_facts', {})
                if ansible_facts:
                    logging.debug(f"ansible_facts keys: {list(ansible_facts.keys())[:10]}")
                    # Try to get IP address from facts
                    ip = self._extract_ip_from_facts(ansible_facts)
                    if ip and ip != host_name:
                        self.host_ok[ip] = result
                        logging.info(f"Also stored result by IP: {ip}")
        except Exception as e:
            logging.error(f"Error in v2_runner_on_ok: {e}")
            import traceback
            logging.error(traceback.format_exc())
    
    def v2_runner_on_failed(self, result, *args, **kwargs):
        """Called when a task fails"""
        logging.info("v2_runner_on_failed called!")
        try:
            host_name = self._get_host_name(result)
            logging.info(f"v2_runner_on_failed: host_name={host_name}")
            self.host_failed[host_name] = result
        except Exception as e:
            logging.error(f"Error in v2_runner_on_failed: {e}")
            import traceback
            logging.error(traceback.format_exc())
    
    def v2_runner_on_unreachable(self, result, *args, **kwargs):
        """Called when a host is unreachable"""
        logging.info("v2_runner_on_unreachable called!")
        try:
            host_name = self._get_host_name(result)
            logging.info(f"v2_runner_on_unreachable: host_name={host_name}")
            self.host_unreachable[host_name] = result
        except Exception as e:
            logging.error(f"Error in v2_runner_on_unreachable: {e}")
            import traceback
            logging.error(traceback.format_exc())
    
    def v2_runner_on_skipped(self, result, *args, **kwargs):
        """Called when a task is skipped"""
        logging.info("v2_runner_on_skipped called!")
        try:
            host_name = self._get_host_name(result)
            logging.info(f"v2_runner_on_skipped: host_name={host_name}")
            self.host_skipped[host_name] = result
        except Exception as e:
            logging.error(f"Error in v2_runner_on_skipped: {e}")
            import traceback
            logging.error(traceback.format_exc())
    
    def v2_playbook_on_play_start(self, play):
        """Called when a play starts"""
        self._playbook_start_called = True
        logging.info("v2_playbook_on_play_start called!")
        try:
            if hasattr(play, 'hosts'):
                logging.info(f"Play hosts: {play.hosts}")
            if hasattr(play, 'name'):
                logging.info(f"Play name: {play.name}")
        except Exception as e:
            logging.error(f"Error in v2_playbook_on_play_start: {e}")
    
    def v2_playbook_on_task_start(self, task, is_conditional):
        """Called when a task starts"""
        self._task_start_called = True
        logging.info("v2_playbook_on_task_start called!")
        try:
            if hasattr(task, 'action'):
                logging.info(f"Task action: {task.action}")
            if hasattr(task, 'name'):
                logging.info(f"Task name: {task.name}")
        except Exception as e:
            logging.error(f"Error in v2_playbook_on_task_start: {e}")
    
    def v2_runner_item_on_ok(self, result, *args, **kwargs):
        """Called when an item in a loop succeeds"""
        logging.info("v2_runner_item_on_ok called!")
        try:
            host_name = self._get_host_name(result)
            logging.info(f"v2_runner_item_on_ok: host_name={host_name}")
            # Store item results in host_ok as well
            self.host_ok[host_name] = result
        except Exception as e:
            logging.error(f"Error in v2_runner_item_on_ok: {e}")
    
    def _get_host_name(self, result) -> str:
        """Extract host name from result object"""
        if hasattr(result, '_host'):
            host = result._host
            if hasattr(host, 'get_name'):
                return host.get_name()
            elif hasattr(host, 'name'):
                return host.name
        return str(result)
    
    def _extract_ip_from_facts(self, ansible_facts: dict) -> Optional[str]:
        """Extract IP address from ansible facts"""
        try:
            if 'ansible_default_ipv4' in ansible_facts:
                ip = ansible_facts['ansible_default_ipv4'].get('address')
                if ip:
                    return ip
            if 'ansible_all_ipv4_addresses' in ansible_facts and ansible_facts['ansible_all_ipv4_addresses']:
                return ansible_facts['ansible_all_ipv4_addresses'][0]
        except Exception:
            pass
        return None


class AnsibleApi:
    """Ansible API wrapper - supports multiple execution methods"""
    
    def __init__(self, use_subprocess: bool = True):
        """
        Initialize Ansible API
        
        Args:
            use_subprocess: If True, use subprocess method (more reliable).
                          If False, use Ansible API method.
        """
        self.use_subprocess = use_subprocess
        
        if not use_subprocess and not ANSIBLE_AVAILABLE:
            raise ImportError(
                "Ansible API modules are not available. "
                "Please install ansible-core: pip install ansible-core"
            )
        
        # Configure Ansible constants
        try:
            ansible_constants.HOST_KEY_CHECKING = False
        except AttributeError:
            pass
        
        # Initialize options
        self.options = namedtuple(
            "Options", [
                "connection", "module_path", "forks", "become", "become_method",
                "become_user", "check", "diff", "verbosity", "remote_user",
                "private_key_file", "ssh_common_args", "ssh_extra_args",
                "sftp_extra_args", "scp_extra_args", "become_ask_pass",
                "ask_pass", "ask_sudo_pass", "ask_vault_pass", "vault_password_files",
                "new_vault_password_file", "output_file", "one_line", "tree",
                "listhosts", "listtasks", "listtags", "syntax", "check_mode",
                "start_at_task", "force_handlers", "step", "skip_tags",
                "subset", "tags", "run_vault_roles", "run_vault_tags"
            ]
        )(
            connection='smart',
            module_path=None,
            forks=5,
            become=None,
            become_method=None,
            become_user=None,
            check=False,
            diff=False,
            verbosity=0,
            remote_user=None,
            private_key_file=None,
            ssh_common_args=None,
            ssh_extra_args=None,
            sftp_extra_args=None,
            scp_extra_args=None,
            become_ask_pass=False,
            ask_pass=False,
            ask_sudo_pass=False,
            ask_vault_pass=False,
            vault_password_files=[],
            new_vault_password_file=None,
            output_file=None,
            one_line=False,
            tree=None,
            listhosts=False,
            listtasks=False,
            listtags=False,
            syntax=False,
            check_mode=False,
            start_at_task=None,
            force_handlers=False,
            step=False,
            skip_tags=[],
            subset=None,
            tags=[],
            run_vault_roles=True,
            run_vault_tags=True
        )
        
        self.passwords = {}
        self.hosts_file = None
        self.exec_hosts = None
        self.tasks = None

    def set_options(self, hosts_file: Optional[str] = None,
                   exec_hosts: Optional[str] = None,
                   tasks: Optional[List[Dict]] = None):
        """Set Ansible execution options"""
        if hosts_file:
            self.hosts_file = hosts_file
        if exec_hosts:
            self.exec_hosts = exec_hosts
        if tasks:
            self.tasks = tasks

    def run_task(self) -> Dict[str, Dict[str, Any]]:
        """Run Ansible playbook and return results"""
        if not self.hosts_file or not self.exec_hosts or not self.tasks:
            raise ValueError("hosts_file, exec_hosts, and tasks must be set before running")
        
        if self.use_subprocess:
            return self._run_with_subprocess()
        else:
            return self._run_with_api()
    
    def _run_with_subprocess(self) -> Dict[str, Dict[str, Any]]:
        """
        Method 1: Use subprocess to call ansible ad-hoc command (most reliable)
        This method uses ansible ad-hoc command with setup module
        """
        logging.info("Using subprocess method to execute Ansible ad-hoc command")
        
        # Extract group name from hosts file
        group_name = self._extract_group_from_hosts_file() or 'all'
        
        # Get the module and arguments from tasks
        # For setup module, we just need the module name
        module_name = 'setup'
        module_args = ''
        
        if self.tasks and len(self.tasks) > 0:
            task = self.tasks[0]
            if 'action' in task and 'module' in task['action']:
                module_name = task['action']['module']
            if 'action' in task and 'args' in task['action']:
                # Convert args dict to string format for ansible
                args_dict = task['action']['args']
                if isinstance(args_dict, dict):
                    # Convert dict to key=value format
                    args_list = [f"{k}={v}" for k, v in args_dict.items()]
                    module_args = ' '.join(args_list)
                else:
                    module_args = str(args_dict)
        
        try:
            # Use ansible command with setup module
            cmd = [
                'ansible',
                group_name,
                '-i', self.hosts_file,
                '-m', module_name
            ]
            
            if module_args:
                cmd.extend(['-a', module_args])
            
            # Set environment variables for Ansible
            env = os.environ.copy()
            # Disable host key checking for SSH
            env['ANSIBLE_HOST_KEY_CHECKING'] = 'False'
            # Disable SSH key checking
            env['ANSIBLE_SSH_ARGS'] = '-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
            # Set remote temporary directory to /tmp (more reliable than ~/.ansible/tmp)
            # This avoids permission issues when user home directory is not writable
            env['ANSIBLE_REMOTE_TMP'] = '/tmp/.ansible'
            logging.info(f"Executing: {' '.join(cmd)}")
            
            # Execute ansible command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                check=False,  # Don't raise on non-zero exit
                env=env
            )
            
            logging.info(f"Ansible ad-hoc exit code: {result.returncode}")
            if result.stdout:
                logging.info(f"Ansible ad-hoc stdout (first 2000 chars):\n{result.stdout[:2000]}")
            if result.stderr:
                logging.warning(f"Ansible ad-hoc stderr (first 2000 chars):\n{result.stderr[:2000]}")
            
            # Parse the output
            results = self._parse_ansible_ad_hoc_output(result.stdout, result.stderr, result.returncode, group_name)
            
            return results
            
        except subprocess.TimeoutExpired:
            logging.error("Ansible execution timed out")
            raise RuntimeError("Ansible execution timed out")
        except FileNotFoundError:
            logging.error("ansible command not found. Please install ansible-core.")
            raise RuntimeError("ansible command not found. Please install ansible-core.")
        except Exception as e:
            logging.error(f"Error executing ansible: {e}")
            import traceback
            logging.error(traceback.format_exc())
            raise
    
    def _run_ansible_ad_hoc_for_facts(self, group_name: str, playbook_output: str) -> Dict[str, Dict[str, Any]]:
        """
        Run ansible ad-hoc command with setup module to get facts in a parseable format
        This is a workaround since ansible-playbook output is hard to parse
        """
        logging.info("Running ansible ad-hoc command to get facts...")
        
        try:
            # Use ansible command with setup module
            cmd = [
                'ansible',
                group_name,
                '-i', self.hosts_file,
                '-m', 'setup',
                '--one-line'  # One line per host
            ]
            
            env = os.environ.copy()
            # Set remote temporary directory to /tmp (more reliable than ~/.ansible/tmp)
            env['ANSIBLE_REMOTE_TMP'] = '/tmp/.ansible'
            logging.info(f"Executing: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
                env=env
            )
            
            logging.info(f"Ansible ad-hoc exit code: {result.returncode}")
            if result.stdout:
                logging.debug(f"Ansible ad-hoc stdout (first 2000 chars):\n{result.stdout[:2000]}")
            if result.stderr:
                logging.debug(f"Ansible ad-hoc stderr (first 1000 chars):\n{result.stderr[:1000]}")
            
            # Parse the output
            results = self._parse_ansible_ad_hoc_output(result.stdout, result.stderr, result.returncode, group_name)
            
            return results
            
        except Exception as e:
            logging.error(f"Error running ansible ad-hoc command: {e}")
            import traceback
            logging.error(traceback.format_exc())
            # Return empty results
            return {
                "success": {},
                "failed": {},
                "unreachable": {}
            }
    
    def _parse_ansible_ad_hoc_output(self, stdout: str, stderr: str, exit_code: int, group_name: str) -> Dict[str, Dict[str, Any]]:
        """
        Parse ansible ad-hoc command output
        Format: hostname | SUCCESS => {...} or hostname | FAILED! => {...} or hostname | UNREACHABLE! => {...}
        Note: JSON can be multi-line
        """
        results = {
            "success": {},
            "failed": {},
            "unreachable": {}
        }
        
        if not stdout:
            logging.warning("No stdout from ansible ad-hoc command")
            if stderr:
                error_msg = f"Ansible ad-hoc command failed: {stderr}"
                logging.error(error_msg)
                if exit_code != 0:
                    raise RuntimeError(error_msg)
            return results
        
        try:
            # Parse output - ansible output can be multi-line JSON
            # Format: hostname | STATUS => {JSON (can be multi-line)}
            # We need to find the pattern and extract the JSON part
            
            # Split by lines but keep track of multi-line JSON
            lines = stdout.split('\n')
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if not line:
                    i += 1
                    continue
                
                # Look for pattern: hostname | STATUS =>
                if '|' not in line or '=>' not in line:
                    i += 1
                    continue
                
                # Split by | to get hostname and status+json
                parts = line.split('|', 1)
                if len(parts) != 2:
                    i += 1
                    continue
                
                hostname = parts[0].strip()
                status_and_json = parts[1].strip()
                
                # Extract status
                if '=>' not in status_and_json:
                    i += 1
                    continue
                
                status_part, json_start = status_and_json.split('=>', 1)
                status = status_part.strip().upper()
                
                # Now we need to extract the JSON, which might be multi-line
                # Find where JSON starts (after =>)
                json_lines = []
                json_str = json_start.strip()
                
                # If JSON starts with {, we need to find the matching }
                if json_str.startswith('{'):
                    brace_count = json_str.count('{') - json_str.count('}')
                    json_lines.append(json_str)
                    
                    # Continue reading lines until braces are balanced
                    i += 1
                    while i < len(lines) and brace_count > 0:
                        line = lines[i]
                        json_lines.append(line)
                        brace_count += line.count('{') - line.count('}')
                        i += 1
                    
                    json_str = '\n'.join(json_lines)
                else:
                    # Single line JSON or not starting with {
                    i += 1
                
                # Try to parse JSON
                try:
                    data = json.loads(json_str)
                    
                    # Determine result category based on status
                    if 'UNREACHABLE' in status:
                        results["unreachable"][hostname] = data
                        logging.info(f"Parsed unreachable result for host: {hostname}")
                    elif 'FAILED' in status:
                        results["failed"][hostname] = data
                        logging.info(f"Parsed failed result for host: {hostname}")
                    elif 'SUCCESS' in status or 'CHANGED' in status:
                        # Check if it's actually successful
                        if isinstance(data, dict) and data.get('failed', False):
                            results["failed"][hostname] = data
                        else:
                            results["success"][hostname] = data
                            logging.info(f"Parsed success result for host: {hostname}")
                    else:
                        # Unknown status, try to infer from data
                        if isinstance(data, dict):
                            if data.get('unreachable', False):
                                results["unreachable"][hostname] = data
                            elif data.get('failed', False):
                                results["failed"][hostname] = data
                            else:
                                results["success"][hostname] = data
                                logging.info(f"Parsed result (unknown status) for host: {hostname}")
                except json.JSONDecodeError as e:
                    logging.warning(f"Failed to parse JSON for host {hostname}: {e}")
                    logging.debug(f"JSON string (first 500 chars): {json_str[:500]}")
                    # Even if JSON parsing fails, we can still extract useful info
                    if 'FAILED' in status:
                        # Try to extract error message from the text
                        error_msg = "Unknown error"
                        if '"msg"' in json_str:
                            # Try to extract msg field
                            msg_match = re.search(r'"msg"\s*:\s*"([^"]+)"', json_str)
                            if msg_match:
                                error_msg = msg_match.group(1)
                        results["failed"][hostname] = {
                            "_msg": error_msg,
                            "_raw_output": json_str[:1000]  # Store raw output for debugging
                        }
                        logging.info(f"Extracted error message for host {hostname}: {error_msg}")
                    elif 'UNREACHABLE' in status:
                        results["unreachable"][hostname] = {
                            "_msg": "Host unreachable",
                            "_raw_output": json_str[:1000]
                        }
                    continue
            
            logging.info(f"Parsed results: success={len(results['success'])}, failed={len(results['failed'])}, unreachable={len(results['unreachable'])}")
            
        except Exception as e:
            logging.error(f"Error parsing ansible ad-hoc output: {e}")
            import traceback
            logging.error(traceback.format_exc())
            # If parsing fails but exit code is 0, try to extract basic info
            if exit_code == 0 and stdout:
                # Maybe the output format is different, try to find hostname and basic info
                logging.warning("Standard parsing failed, attempting fallback parsing...")
                # Look for IP addresses or hostnames in output
                ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
                ips = re.findall(ip_pattern, stdout)
                if ips:
                    # Use first IP found as hostname
                    hostname = ips[0]
                    if 'SUCCESS' in stdout.upper() or 'CHANGED' in stdout.upper():
                        results["success"][hostname] = {"_msg": "Task completed but output format unexpected", "_raw": stdout[:500]}
                    elif 'FAILED' in stdout.upper():
                        results["failed"][hostname] = {"_msg": "Task failed", "_raw": stdout[:500]}
                    elif 'UNREACHABLE' in stdout.upper():
                        results["unreachable"][hostname] = {"_msg": "Host unreachable", "_raw": stdout[:500]}
        
        # Final validation
        if len(results["success"]) == 0 and len(results["failed"]) == 0 and len(results["unreachable"]) == 0:
            error_msg = (
                f"Ansible ad-hoc command executed but no results were collected. "
                f"This usually means:\n"
                f"  1. The hosts '{group_name}' did not match any hosts in the inventory\n"
                f"  2. All tasks were skipped or filtered out\n"
                f"  3. An unexpected output format was received.\n"
                f"Please check the inventory file and command output.\n"
                f"Stdout: {stdout[:500]}\n"
                f"Stderr: {stderr[:500] if stderr else 'None'}"
            )
            logging.error(error_msg)
            if exit_code != 0:
                raise RuntimeError(error_msg)
            else:
                logging.warning("Exit code was 0 but no results found - this may be expected if no hosts matched")
        
        return results
    
    def _run_with_api(self) -> Dict[str, Dict[str, Any]]:
        """
        Method 2: Use Ansible API (TaskQueueManager)
        This method uses the Ansible Python API directly
        """
        logging.info("Using Ansible API method to execute playbook")
        
        # Initialize Ansible components
        loader = DataLoader()
        inventory = InventoryManager(loader=loader, sources=[self.hosts_file])
        variable_manager = VariableManager(loader=loader, inventory=inventory)
        results_callback = ResultCallback()
        
        # Determine play hosts (group name or IP)
        play_hosts = self._determine_play_hosts(inventory)
        logging.info(f"Using play hosts: {play_hosts}")
        
        # Create play source - use IP directly if group doesn't work
        play_source = {
            "name": "Ansible Play",
            "hosts": play_hosts,
            "tasks": self.tasks,
            "gather_facts": "no"
        }
        logging.info(f"Play source: hosts={play_hosts}, tasks count={len(self.tasks)}")
        
        # Load play
        play = Play().load(
            play_source,
            variable_manager=variable_manager,
            loader=loader
        )
        
        # Verify hosts in inventory
        self._verify_inventory_hosts(inventory, play_hosts)
        
        # Create TaskQueueManager
        tqm = None
        try:
            tqm = TaskQueueManager(
                inventory=inventory,
                variable_manager=variable_manager,
                loader=loader,
                passwords=self.passwords,
                stdout_callback=results_callback,
                run_additional_callbacks=True,
                run_tree=False,
                forks=5
            )
            logging.info("TaskQueueManager created successfully")
            
            # Execute play
            logging.info("Starting play execution...")
            tqm.run(play)
            logging.info("Play execution completed")
            
            # Process results
            results = self._process_results(results_callback, tqm)
            
            return results
            
        finally:
            if tqm is not None:
                tqm.cleanup()
            self._cleanup_temp_dir()
    
    def _determine_play_hosts(self, inventory: InventoryManager) -> str:
        """Determine the play hosts (group name or IP)"""
        play_hosts = None
        
        try:
            # Try to get groups from inventory
            groups_dict = {}
            if hasattr(inventory, 'get_groups_dict'):
                groups_dict = inventory.get_groups_dict()
            elif hasattr(inventory, 'groups'):
                groups_dict = dict(inventory.groups)
            elif hasattr(inventory, '_inventory') and hasattr(inventory._inventory, 'groups'):
                groups_dict = dict(inventory._inventory.groups)
            
            if groups_dict:
                logging.info(f"Inventory groups: {list(groups_dict.keys())}")
                
                # Find group containing exec_hosts IP
                for group_name, group in groups_dict.items():
                    if group_name in ['all', 'ungrouped']:
                        continue
                    
                    hosts_in_group = []
                    if hasattr(group, 'get_hosts'):
                        hosts_in_group = [h.name for h in group.get_hosts()]
                    elif hasattr(group, 'hosts'):
                        hosts_in_group = [h.name if hasattr(h, 'name') else str(h) for h in group.hosts]
                    
                    logging.info(f"Group '{group_name}' contains hosts: {hosts_in_group}")
                    
                    if self.exec_hosts in hosts_in_group:
                        play_hosts = group_name
                        logging.info(f"Found exec_hosts {self.exec_hosts} in group '{group_name}'")
                        break
                
                # If not found, use first non-all/ungrouped group
                if play_hosts is None:
                    for group_name in groups_dict.keys():
                        if group_name not in ['all', 'ungrouped']:
                            play_hosts = group_name
                            logging.info(f"Using first available group '{group_name}' for play")
                            break
            else:
                # Fallback: extract group name from hosts file
                play_hosts = self._extract_group_from_hosts_file()
        
        except Exception as e:
            logging.warning(f"Error analyzing inventory: {e}")
            import traceback
            logging.debug(traceback.format_exc())
            play_hosts = self._extract_group_from_hosts_file()
        
        # Final fallback to exec_hosts
        if play_hosts is None:
            play_hosts = self.exec_hosts
            logging.warning(f"No suitable group found, using exec_hosts '{play_hosts}' directly")
        
        return play_hosts
    
    def _extract_group_from_hosts_file(self) -> Optional[str]:
        """Extract group name from hosts file"""
        try:
            with open(self.hosts_file, 'r') as f:
                content = f.read()
                match = re.search(r'\[([^\]]+)\]', content)
                if match:
                    group_name = match.group(1)
                    logging.info(f"Extracted group name '{group_name}' from hosts file")
                    return group_name
        except Exception as e:
            logging.warning(f"Could not parse hosts file: {e}")
        return None
    
    def _verify_inventory_hosts(self, inventory: InventoryManager, play_hosts: str):
        """Verify that hosts exist in inventory"""
        try:
            if hasattr(inventory, 'get_hosts'):
                inventory_hosts = inventory.get_hosts(play_hosts)
                host_names = [h.name for h in inventory_hosts] if inventory_hosts else []
                logging.info(f"Inventory group '{play_hosts}' contains {len(host_names)} hosts: {host_names}")
                
                if len(host_names) == 0:
                    logging.error(f"ERROR: Inventory group '{play_hosts}' has no hosts!")
                    # Try using IP directly
                    if self.exec_hosts and self.exec_hosts != play_hosts:
                        direct_hosts = inventory.get_hosts(self.exec_hosts)
                        if direct_hosts:
                            logging.info(f"Found host '{self.exec_hosts}' directly in inventory")
                elif self.exec_hosts not in host_names:
                    logging.warning(f"WARNING: exec_hosts '{self.exec_hosts}' not found in group '{play_hosts}' hosts: {host_names}")
        except Exception as e:
            logging.warning(f"Could not verify inventory hosts: {e}")
    
    def _process_results(self, callback: Optional[ResultCallback], tqm: Optional[TaskQueueManager]) -> Dict[str, Dict[str, Any]]:
        """Process callback results and return formatted dictionary"""
        results = {
            "success": {},
            "failed": {},
            "unreachable": {}
        }
        
        logging.info("Processing callback results...")
        
        # Process callback results (if callback is provided)
        if callback:
            for host, result in callback.host_ok.items():
                result_data = result._result if hasattr(result, '_result') else result
                results["success"][host] = result_data
                logging.info(f"Added success result for host: {host}")
            
            for host, result in callback.host_failed.items():
                result_data = result._result if hasattr(result, '_result') else result
                results["failed"][host] = result_data
                logging.info(f"Added failed result for host: {host}")
            
            for host, result in callback.host_unreachable.items():
                result_data = result._result if hasattr(result, '_result') else result
                results["unreachable"][host] = result_data
                logging.info(f"Added unreachable result for host: {host}")
            
            # If no results from callback, try to extract from TQM stats
            if len(results["success"]) == 0 and len(results["failed"]) == 0 and len(results["unreachable"]) == 0:
                logging.warning("No results from callback, trying to extract from TQM stats...")
                if tqm:
                    self._extract_results_from_stats(tqm, results)
            
            # Check callback status
            total_callbacks = len(results["success"]) + len(results["failed"]) + len(results["unreachable"])
            if total_callbacks == 0:
                logging.error("ERROR: No callback methods were called!")
                if callback:
                    logging.error(f"Playbook start callback called: {callback._playbook_start_called}")
                    logging.error(f"Task start callback called: {callback._task_start_called}")
                if tqm:
                    self._log_tqm_stats(tqm)
            else:
                logging.info(f"Callbacks were triggered: {total_callbacks} total results")
        
        logging.info(f"Final results: success={len(results['success'])}, failed={len(results['failed'])}, unreachable={len(results['unreachable'])}")
        
        # Validate results
        if len(results["success"]) == 0 and len(results["failed"]) == 0 and len(results["unreachable"]) == 0:
            error_msg = (
                f"Ansible playbook executed but no results were collected. "
                f"This usually means:\n"
                f"  1. The play hosts did not match any hosts in the inventory\n"
                f"  2. All tasks were skipped or filtered\n"
                f"  3. The callback was not properly invoked\n"
                f"Please check the inventory file and play configuration."
            )
            logging.error(error_msg)
            raise RuntimeError(error_msg)

        return results

    def _extract_results_from_stats(self, tqm: Optional[TaskQueueManager], results: Dict):
        """Extract results from TQM stats as fallback"""
        try:
            if tqm and hasattr(tqm, '_stats'):
                stats = tqm._stats
                # Check for successful hosts
                if hasattr(stats, 'ok') and stats.ok:
                    for host in stats.ok.keys():
                        logging.warning(f"Found host '{host}' in stats.ok but not in callback")
                        results["success"][host] = {
                            "_msg": "Task completed but result not captured by callback",
                            "_stats_ok": True
                        }
                # Check for failed hosts
                if hasattr(stats, 'failed') and stats.failed:
                    for host in stats.failed.keys():
                        logging.warning(f"Found host '{host}' in stats.failed but not in callback")
                        results["failed"][host] = {
                            "_msg": "Task failed but result not captured by callback",
                            "_stats_failed": True
                        }
                # Check for unreachable hosts
                if hasattr(stats, 'unreachable') and stats.unreachable:
                    for host in stats.unreachable.keys():
                        logging.warning(f"Found host '{host}' in stats.unreachable but not in callback")
                        results["unreachable"][host] = {
                            "_msg": "Host unreachable but result not captured by callback",
                            "_stats_unreachable": True
                        }
        except Exception as e:
            logging.warning(f"Could not extract results from TQM stats: {e}")
            import traceback
            logging.debug(traceback.format_exc())
    
    def _log_tqm_stats(self, tqm: Optional[TaskQueueManager]):
        """Log TQM stats for debugging"""
        try:
            if tqm and hasattr(tqm, '_stats'):
                stats = tqm._stats
                logging.error(f"TQM stats object: {stats}")
                if hasattr(stats, 'ok'):
                    logging.error(f"Stats ok: {dict(stats.ok)}")
                if hasattr(stats, 'failed'):
                    logging.error(f"Stats failed: {dict(stats.failed)}")
                if hasattr(stats, 'unreachable'):
                    logging.error(f"Stats unreachable: {dict(stats.unreachable)}")
                if hasattr(stats, 'skipped'):
                    logging.error(f"Stats skipped: {dict(stats.skipped)}")
        except Exception as e:
            logging.debug(f"Could not log TQM stats: {e}")
    
    def _cleanup_temp_dir(self):
        """Clean up temporary Ansible directory"""
        try:
            if ANSIBLE_AVAILABLE:
                tmp_dir = getattr(ansible_constants, 'DEFAULT_LOCAL_TMP', '/tmp/.ansible')
                if os.path.exists(tmp_dir):
                    shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass